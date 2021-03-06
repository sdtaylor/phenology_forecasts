import xarray as xr
import pandas as pd
import numpy as np
from tools import tools
from tools.phenology_tools import predict_phenology_from_climate
import os
import datetime
import time
import glob
from pyPhenology import utils



def run(climate_forecast_folder = None, 
        phenology_forecast_folder = None,
        species_list = None):
    """Build phenology models
    
    """
    divider='#'*90
    
    config = tools.load_config()
    
    current_season=tools.current_growing_season(config)
    current_season_doy_0 = str(int(current_season)) + '0101'
    current_season_doy_0 = tools.string_to_date(current_season_doy_0, h=False).date()
    today = datetime.datetime.today().date()
  
    current_doy = today.timetuple().tm_yday
    season_first_date = str(int(current_season)-1) + config['season_month_begin'] + config['season_day_begin']
    season_first_date = tools.string_to_date(season_first_date, h=False).date()
    
    # if the season for spring forecasts has started. Nov 1
    if today >= season_first_date:
        # adjust the current doy to potentially be negative to reflect the doy
        # for the following calendar year.
        if today < current_season_doy_0:
            current_doy -= 365
    
    print(divider)
    print('Applying phenology models - ' + str(today))
    
    range_masks = xr.open_dataset(config['species_range_file'])
    
    doy_0 = np.datetime64(current_season_doy_0)
    
    # Default location of climate forecasts
    if not climate_forecast_folder:
        climate_forecast_folder = config['current_forecast_folder']
        
    current_climate_forecast_files = glob.glob(climate_forecast_folder+'*.nc')
    
    print(str(len(current_climate_forecast_files)) + ' current climate forecast files: \n' + str(current_climate_forecast_files))
    
    # Load default species list if no special one was passed
    if not species_list:
        species_list = pd.read_csv(config['species_list_file'])
        species_list = species_list[['species','Phenophase_ID','current_forecast_version',
                                     'season_start_doy','season_end_doy']]
        
    # Only forecast species and phenophases in the current season
    species_list = species_list[(current_doy >= species_list.season_start_doy) & (current_doy <= species_list.season_end_doy)]
    
    if len(species_list) == 0:
        raise RuntimeError('No species currenly in season, which is roughly Dec. 1 - Nov. 1')
    
    phenology_model_metadata = pd.read_csv(config['phenology_model_metadata_file'])
    
    forecast_metadata = species_list.merge(phenology_model_metadata, 
                                           left_on =['species','Phenophase_ID','current_forecast_version'],
                                           right_on=['species','Phenophase_ID','forecast_version'], 
                                           how='left')
    
    # Default location to write phenology forecasts
    if not phenology_forecast_folder:
        phenology_forecast_folder = config['phenology_forecast_folder']
    
    print(divider)
    
    # Load the climate forecasts
    
    #current_climate_forecasts = [xr.open_dataset(f) for f in current_climate_forecast_files]
    
    num_species_processed=0
    for i, forecast_info in enumerate(forecast_metadata.to_dict('records')):
        species = forecast_info['species']
        phenophase = forecast_info['Phenophase_ID']
        model_file = config['phenology_model_folder']+forecast_info['model_file']
        model = utils.load_saved_model(model_file)
        
        print(divider)
        if species not in range_masks.species.values:
            print('Skipping {s} {p}, no range mask'.format(s=species, p=phenophase))
            continue
        else:
            print('Apply model for {s} {p}'.format(s=species, p=phenophase))
            print('forecast attempt {i} of {n} potential species. {n2} processed succesfully so far.'.format(i=i, n=len(forecast_metadata), n2=num_species_processed))
            species_range = range_masks.sel(species=species)
    
    
        prediction, prediction_sd = predict_phenology_from_climate(model,
                                                                   current_climate_forecast_files,
                                                                   post_process='automated',
                                                                   doy_0=doy_0,
                                                                   species_range=species_range,
                                                                   n_jobs=config['n_jobs'])
        
        species_forecast = xr.Dataset(data_vars = {'doy_prediction':(('species','phenophase', 'lat','lon'), prediction),
                                                   'doy_sd':(('species', 'phenophase', 'lat','lon'), prediction_sd)},
                                      coords = {'species':[species], 'phenophase':[phenophase],
                                              'lat':species_range.lat, 'lon':species_range.lon})
    
        if i==0:
            all_species_forecasts = species_forecast
            num_species_processed+=1
        else:
            merge_start_time=time.time()
            all_species_forecasts = xr.merge([all_species_forecasts,species_forecast])
            print('merge time {s} sec'.format(s=round(time.time() - merge_start_time,0)))
            num_species_processed+=1
    
        # Merging this files over and over slows things down more and more
        # Saving it every few iterations seems to speed things up. 
        if num_species_processed % 5 == 0:
            all_species_forecasts.to_netcdf(config['tmp_folder']+'forecast_tmp.nc')
            all_species_forecasts = xr.open_dataset(config['tmp_folder']+'forecast_tmp.nc')
            all_species_forecasts.load()
            all_species_forecasts.close()
    
    print(divider)
    print('phenology forecast final processing')
    #all_species_forecasts = xr.merge(all_species_forecasts)
    
    current_season = tools.current_growing_season(config)
    
    provenance_note = \
    """Forecasts for plant phenology of select species flowering and/or leaf out
    times for the {s} season. Made on {t} from NOAA CFSv2
    forecasts downscaled using PRISM climate data.
    Plant phenology models made using National Phenology Network data. 
    """.format(s=current_season, t=today)
    
    all_species_forecasts.attrs['note']=provenance_note
    all_species_forecasts.attrs['issue_date']=str(today)
    all_species_forecasts.attrs['crs']='+init=epsg:4269'
    # TODO: add some  more metadata
    # common names?
    #all_species_forecasts['forecast_date']=str(today)
    #all_species_forecasts['forecast_date']=str(today)
    
    forecast_filename = config['phenology_forecast_folder']+'phenology_forecast_'+str(today)+'.nc'
    
    all_species_forecasts = all_species_forecasts.chunk({'lat':50,'lon':50})
    all_species_forecasts.to_netcdf(forecast_filename, encoding={'doy_prediction':{'zlib':True,
                                                                                   'complevel':4, 
                                                                                   'dtype':'int32', 
                                                                                   'scale_factor':0.001,  
                                                                                   '_FillValue': -9999},
                                                                         'doy_sd':{'zlib':True,
                                                                                   'complevel':4, 
                                                                                   'dtype':'int32', 
                                                                                   'scale_factor':0.001,  
                                                                                   '_FillValue': -9999}})

    # Return filename of final forecast file for use by primary script
    return forecast_filename

if __name__=='__main__':
    run()
