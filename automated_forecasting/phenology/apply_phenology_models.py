import xarray as xr
import pandas as pd
import numpy as np
from tools import tools
import os
import datetime
import time
import glob
from pyPhenology import utils



def run():
    divider='#'*90
    
    config = tools.load_config()
    
    today = datetime.datetime.today().date()
    
    print(divider)
    print('Applying phenology models - ' + str(today))
    
    range_masks = xr.open_dataset(config['species_range_file'])
    
    doy_0 = np.datetime64('2018-01-01')
    
    current_climate_forecast_files = glob.glob(config['current_forecast_folder']+'*.nc')
    
    print(str(len(current_climate_forecast_files)) + ' current climate forecast files: \n' + str(current_climate_forecast_files))
    
    species_list = pd.read_csv(config['species_list_file'])
    species_list = species_list[['species','Phenophase_ID','current_forecast_version']]
    phenology_model_metadata = pd.read_csv(config['phenology_model_metadata_file'])
    
    forecast_metadata = species_list.merge(phenology_model_metadata, 
                                           left_on =['species','Phenophase_ID','current_forecast_version'],
                                           right_on=['species','Phenophase_ID','forecast_version'], 
                                           how='left')
    
    print(divider)
    
    # Load the climate forecasts
    
    current_climate_forecasts = [xr.open_dataset(f) for f in current_climate_forecast_files]
    
    num_species_processed=0
    for i, forecast_info in enumerate(forecast_metadata.to_dict('records')):
        species = forecast_info['species']
        phenophase = forecast_info['Phenophase_ID']
        model_file = config['phenology_model_folder']+forecast_info['model_file']
        base_model_name = forecast_info['base_model']
        model = utils.load_saved_model(model_file)
        
        print(divider)
        if species not in range_masks.species.values:
            print('Skipping {s} {p}, no range mask'.format(s=species, p=phenophase))
            continue
        else:
            print('Apply model for {s} {p}'.format(s=species, p=phenophase))
            print('forecast attempt {i} of {n} potential species. {n2} processed succesfully so far.'.format(i=i, n=len(forecast_metadata), n2=num_species_processed))
            species_range = range_masks.sel(species=species)
    
    
    
        species_ensemble = []
        for climate in current_climate_forecasts:
            doy_series =  pd.TimedeltaIndex(climate.time.values - doy_0, freq='D').days.values
            
            species_ensemble.append(model.predict(predictors={'temperature': climate.tmean.values,
                                                              'doy_series' : doy_series}))
        
        species_ensemble = np.array(species_ensemble).astype(np.float)
        # apply nan to non predictions
        species_ensemble[species_ensemble==999]=np.nan
        
        # Keep only values in the range
        species_ensemble[:,~species_range.range.values]=np.nan
        
        prediction = np.mean(species_ensemble, axis=0)
        prediction_sd = np.std(species_ensemble, axis=0)
        
        # extend the axis by 2 to match the xarray creation
        prediction = np.expand_dims(prediction, axis=0)
        prediction = np.expand_dims(prediction, axis=0)
        prediction_sd = np.expand_dims(prediction_sd, axis=0)
        prediction_sd = np.expand_dims(prediction_sd, axis=0)
        
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
