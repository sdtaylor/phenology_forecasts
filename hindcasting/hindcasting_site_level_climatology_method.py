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

#doy_0 = np.datetime64(hindcast_config.doy_0)

today = datetime.datetime.today().date()

# For spatial reference
land_mask = xr.open_dataset(config['mask_file'])

####################
# Climate files
# 20 years of daily temperature
historic_temp_filenames = glob.glob(config['historic_observations_folder']+'yearly/prism_tmean*')                                                                                                                                                       
historic_temperature = xr.open_mfdataset(historic_temp_filenames)
historic_years = np.unique([t.year for t in historic_temperature.time.to_series()])

# don't use the first year cause data from the prior year is needed
historic_years = historic_years[1:]

# Align the latitude and longitude as they can become mismatched due 
# to rounding errors
#historic_temperature['lat'] = current_season_temperature['lat']
#historic_temperature['lon'] = current_season_temperature['lon']

######################################################
#from joblib import parallel_backend
#from dask import delayed, compute
#from dask.distributed import Client, LocalCluster
from joblib import Parallel, delayed

#cluster = LocalCluster(n_workers=hindcast_config.n_prediction_jobs)
#client = Client(cluster)

######################################################
def dataframe_chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

@delayed
def process_species(model, site_info, site_temp, historic_climate_member, species, Phenophase_ID):
    try:
        prediction_array = model.predict(to_predict=site_info,
                                             predictors=site_temp,
                                             aggregation='none',
                                             n_jobs=-1)
        
                    
        pheno_ensemble_names = [m['parameters'][0]['model_name'] for m in model._get_model_info()['core_models']]
        num_bootstraps = len(model.model_list[0].model_list)
        
        # prediction_array is a 3D 'phenology_esemble' x 'bootstrap' x 'site' array,
        # use xarray to easily label it and convert to dataframe
        prediction_dataframe = xr.DataArray(prediction_array, dims=('phenology_model','bootstrap','site_id'),
                                        name='doy_prediction',
                                        coords={'phenology_model':pheno_ensemble_names,
                                                'bootstrap': range(num_bootstraps),
                                                'site_id': site_info.site_id}).to_dataframe().reset_index()
        
        prediction_dataframe['species'] = species
        prediction_dataframe['Phenophase_ID'] = Phenophase_ID
        prediction_dataframe['issue_date'] = '2000-01-01' # climatology method does not use issue dates, so use an absurd one to make sure I catch it later on.
        prediction_dataframe['climate_member'] = historic_climate_member
        
        return prediction_dataframe
    except:
        return pd.DataFrame()

def extract_single_site_temp(clim, site):
    site_climate_chunk = clim.sel(lat = site.lat.values, 
                                  lon = site.lon.values, 
                                  method='nearest')
    site['climate_lon'] = site_climate_chunk.lon
    site['climate_lat'] = site_climate_chunk.lat
            
    site_climate_chunk = site_climate_chunk.to_dataframe().dropna().reset_index()
            
    site_climate_chunk.rename(index=str, columns={'lat':'climate_lat','lon':'climate_lon'}, inplace=True) 
        
    site_temp_chunk = site.merge(site_climate_chunk, how='left',
                                 on=['climate_lon','climate_lat'])

    return site_temp_chunk

# drop leap days from an xr dataset because, just, no.....
def pd_drop_leap_days(timeseries):
    leap_days = np.logical_and(timeseries.month == 2, timeseries.day == 29)
    not_leap_days = np.logical_not(leap_days)
    return timeseries[not_leap_days]

######################################################
# for tracking progress
total_species=len(forecast_metadata)
start_time = time.time()

######################################################
# final results
all_hindcast_predictions = []

for historic_year_i, historic_year in enumerate(historic_years):
    time_elapsed = np.round((time.time() - start_time)/60,0)
    print('Historic year {y}/20, elapsed time {t} minutes'.format(y = historic_year_i,
                                                                  t = time_elapsed))
    
    
    historic_year_start_date = '{y}-11-01'.format(y = historic_year-1)
    historic_year_end_date   = '{y}-08-01'.format(y = historic_year)
    doy_0 = np.datetime64('{y}-01-01'.format(y = historic_year))
    
    
    historic_dates_to_extract = pd.date_range(historic_year_start_date,
                                              historic_year_end_date,
                                              freq='1D')
    
    historic_dates_to_extract = pd_drop_leap_days(historic_dates_to_extract)
    
    # crop the historic climate to the current issue date forward
    historic_temperature_subset = historic_temperature.sel(time = historic_dates_to_extract).copy()
    historic_temperature_subset.load()
    
    # convert dates from the 90's and 2000's to dates for the 2018 season
    #historic_months = pd.DatetimeIndex(historic_temperature_subset.time.values).month
    #historic_days   = pd.DatetimeIndex(historic_temperature_subset.time.values).day
    #adjusted_days = []
    #for d, m in zip(historic_days, historic_months):
    #    y = 2017 if m >=10 else 2018
    #    adjusted_days.append('{y}-{m}-{d}'.format(y=y, m=m, d=d))
    
    #historic_temperature_subset['time'] = pd.DatetimeIndex(adjusted_days)
    
    # combine w/ 2018 temps up to the current issue date
    #historic_climate_member = current_season_temperature_subset.combine_first(historic_temperature_subset)
    #historic_climate_member = xr.merge([current_season_temperature_subset, historic_temperature_subset])
    #historic_climate_member.load()
    #print('year {y}, issue_date {i}, {n} days combined in historic member'.format(y=historic_year,
    #                                                                              i=hindcast_issue_date,
    #                                                                              n=historic_climate_member.dims['time']))
    
    
    ####################################################
    # Get timeseries of daily temp for each site needed for hindcasting
    # I want the temperature at all sites listed in site_info. This does a nearest neighbor lookup,
    # but to associate each time series with a site_id I need to use the lat/lon from the 
    # climate file, which are slighly different than the points in site_info
    site_info_for_prediction = site_info.copy()

    site_temp = pd.DataFrame()
    
    site_temp = Parallel(n_jobs=8)(delayed(extract_single_site_temp)(clim=historic_temperature_subset, site=s.copy()) for s in dataframe_chunker(site_info_for_prediction,1))
    site_temp = pd.concat(site_temp)
    
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
    hindcasts_to_compute = []
    for species_i, forecast_info in enumerate(forecast_metadata.to_dict('records')):
        
        species = forecast_info['species']
        Phenophase_ID = forecast_info['Phenophase_ID']
        model_file = config['phenology_model_folder']+forecast_info['model_file']
        model = utils.load_saved_model(model_file)

        # only make predictions where this species is located.             
        sites_for_this_species = species_sites.query('species == @species & Phenophase_ID == @Phenophase_ID')
        site_info_for_this_species = site_info_for_prediction[site_info_for_prediction.site_id.isin(sites_for_this_species.site_id)]
        site_temp_for_this_species = site_temp[site_temp.site_id.isin(sites_for_this_species.site_id)]
        #print('{s} - {p}'.format(s=species, p=Phenophase_ID))
        #print('################## site info ###################')
        #print(site_info_for_this_species)
        #print('################## site temp ###################')
        #print(site_temp_for_this_species)
        hindcasts_to_compute.append(process_species(model=model,
                                                    site_info = site_info_for_this_species,
                                                    site_temp = site_temp_for_this_species,
                                                    historic_climate_member = historic_year_i+1,
                                                    species = species,
                                                    Phenophase_ID = Phenophase_ID))
        
    all_hindcast_predictions.extend(Parallel(n_jobs=hindcast_config.n_prediction_jobs)(hindcasts_to_compute))

all_hindcast_predictions = pd.concat(all_hindcast_predictions)

all_hindcast_predictions.to_csv(config['data_folder']+ 'evaluation/hindcast_climatology_method_data_2018.csv', index=False)
