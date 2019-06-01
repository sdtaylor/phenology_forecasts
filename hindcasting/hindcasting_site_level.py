import pandas as pd
import numpy as np
import xarray as xr
import glob
import datetime
from time import sleep
import time
from tools import tools
from pyPhenology import utils

import hindcast_config
config = tools.load_config()

begin_date = tools.string_to_date(hindcast_config.begin_date, h=False)
end_date   = tools.string_to_date(hindcast_config.end_date, h=False)
date_range=pd.date_range(begin_date, 
                         end_date,
                         freq = hindcast_config.frequency).to_pydatetime()

######
# Species & phenology modeling stuff
hindcast_species = pd.read_csv(config['data_folder']+'species_for_hindcasting.csv')
phenology_model_metadata = pd.read_csv(config['phenology_model_metadata_file'])
forecast_metadata = hindcast_species.merge(phenology_model_metadata, 
                                                           left_on =['species','Phenophase_ID','current_forecast_version'],
                                                           right_on=['species','Phenophase_ID','forecast_version'], 
                                                           how='left')

#################
# info on where and what to do hindcasts with. 
site_info = pd.read_csv(config['data_folder']+hindcast_config.observation_site_info_file)
site_info.rename(index=str, columns={'Site_ID':'site_id','Latitude':'lat','Longitude':'lon'}, inplace=True)
site_info = site_info[['site_id','lat','lon']]

# not all sites have all species, so load the observation data to pair down
# the  predictions needed. 
species_sites = pd.read_csv(config['data_folder']+hindcast_config.observation_file)

#site_info = site_info.head(100)
#######
# Other stuff

doy_0 = np.datetime64(hindcast_config.doy_0)

today = datetime.datetime.today().date()

# For spatial reference
land_mask = xr.open_dataset(config['mask_file'])

######################################################
def dataframe_chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

######################################################
# for tracking progress
total_dates=len(date_range)
total_species=len(forecast_metadata)
start_time = time.time()

######################################################
# final results
all_hindcast_predictions = pd.DataFrame()

for date_i, hindcast_issue_date in enumerate(date_range):
    ################################################
    # The source data for this issue date
    climate_forecast_folder = config['data_folder']+'past_climate_forecasts/'+str(hindcast_issue_date.date())+'/'
       
    current_climate_forecast_files = glob.glob(climate_forecast_folder+'*.nc')
      
    # Take a peek at the first one to get the timestep count. needed to 
    # set the chunksize correctly.
    num_timesteps = len(xr.open_dataset(current_climate_forecast_files[0]).time)
    latitude_length = len(land_mask.lat)
    longitude_length = len(land_mask.lon)
    
    for climate_i, climate_member_file in enumerate(current_climate_forecast_files):
        climate_member = xr.open_dataset(climate_member_file, chunks={'time':50})
        climate_member.load()
        
        site_info_for_prediction = site_info.copy()
        ####################################################
        # Get timeseries of daily temp for each site needed for hindcasting
        # I want the temperature at all sites listed in site_info. This does a nearest neighbor lookup,
        # but to associate each time series with a site_id I need to use the lat/lon from the 
        # climate file, which are slighly different than the points in site_info
        site_temp = pd.DataFrame()
        
        # Also need to do this step iteravely because big data
        for c in dataframe_chunker(site_info_for_prediction, 1):
            site_climate_chunk = climate_member.sel(lat = c.lat.values, 
                                                  lon = c.lon.values, 
                                                  method='nearest')
            c['climate_lon'] = site_climate_chunk.lon
            c['climate_lat'] = site_climate_chunk.lat
            
            site_climate_chunk = site_climate_chunk.to_dataframe().dropna().reset_index()
            
            site_climate_chunk.rename(index=str, columns={'lat':'climate_lat','lon':'climate_lon'}, inplace=True) 
        
            site_temp_chunk = c.merge(site_climate_chunk, how='left',
                                      on=['climate_lon','climate_lat'])
            #last step
            site_temp = site_temp.append(site_temp_chunk)
        
        
        site_temp['doy'] = pd.TimedeltaIndex(site_temp.time.values - doy_0).days.values
        site_temp = site_temp[['site_id','tmean','doy']]
        site_temp.rename(index=str, columns={'tmean':'temperature'},inplace=True)
        
        # some sites dont have data from being over water or in canada
        sites_without_temp = site_temp.site_id[site_temp.temperature.isna()]
        
        site_info_for_prediction = site_info_for_prediction[~site_info_for_prediction.site_id.isin(sites_without_temp)]
        
        
        # insert dummy year columns needed by predict()
        site_info_for_prediction['year'] = hindcast_config.target_season
        site_temp['year'] = hindcast_config.target_season
        
        ####################################################
        # Apply each model to the climate data
        for species_i, forecast_info in enumerate(forecast_metadata.to_dict('records')):
            
            time_elapsed = np.round((time.time() - start_time)/60,0)
            print('Hindcast date {d}/{D}, species {s}/{S}, elapsed time {t} minutes'.format(d = date_i,
                                                                                            D = total_dates,
                                                                                            s = species_i,
                                                                                            S = total_species,
                                                                                            t = time_elapsed))
            
            species = forecast_info['species']
            Phenophase_ID = forecast_info['Phenophase_ID']
            model_file = config['phenology_model_folder']+forecast_info['model_file']
            model = utils.load_saved_model(model_file)

            # only make predictions where this species is located.             
            sites_for_this_species = species_sites.query('species == @species & Phenophase_ID == @Phenophase_ID')
            site_info_for_this_species = site_info_for_prediction[site_info_for_prediction.site_id.isin(sites_for_this_species.site_id)]
            prediction_array = model.predict(to_predict=site_info_for_this_species,
                                             predictors=site_temp,
                                             aggregation='none',
                                             n_jobs=hindcast_config.n_prediction_jobs)
            
                        
            pheno_ensemble_names = [m['parameters'][0]['model_name'] for m in model._get_model_info()['core_models']]
            num_bootstraps = len(model.model_list[0].model_list)
            
            # prediction_array is a 3D 'phenology_esemble' x 'bootstrap' x 'site' array,
            # use xarray to easily label it and convert to dataframe
            prediction_dataframe = xr.DataArray(prediction_array, dims=('phenology_model','bootstrap','site_id'),
                                            name='doy_prediction',
                                            coords={'phenology_model':pheno_ensemble_names,
                                                    'bootstrap': range(num_bootstraps),
                                                    'site_id': site_info_for_this_species.site_id}).to_dataframe().reset_index()
            
            prediction_dataframe['species'] = species
            prediction_dataframe['Phenophase_ID'] = Phenophase_ID
            prediction_dataframe['issue_date'] = str(hindcast_issue_date.date())
            
            all_hindcast_predictions = all_hindcast_predictions.append(prediction_dataframe)

all_hindcast_predictions.to_csv(hindcast_config.final_hindcast_file, index=False)