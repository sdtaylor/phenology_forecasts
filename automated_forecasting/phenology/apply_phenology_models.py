import xarray as xr
import pandas as pd
import numpy as np
from tools import tools
import os
import datetime
import time
import glob
from pyPhenology import utils
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

all_species_forecasts=[]
for i, forecast_info in enumerate(forecast_metadata.to_dict('records')):
    species = forecast_info['species']
    phenophase = forecast_info['Phenophase_ID']
    model_file = config['phenology_model_folder']+forecast_info['model_file']
    base_model_name = forecast_info['base_model']
    Model = utils.load_model(base_model_name)
    model = Model(parameters=model_file)
    
    print(divider)
    if species not in range_masks.species.values:
        print('Skipping {s} {p}, no range mask'.format(s=species, p=phenophase))
        continue
    else:
        print('Apply model for {s} {p}'.format(s=species, p=phenophase))
        print('forecast {i} of {n}'.format(i=i, n=len(forecast_metadata)))
        species_range = range_masks.sel(species=species)



    species_ensemble = []
    for climate in current_climate_forecasts:
        doy_series =  pd.TimedeltaIndex(climate.time.values - doy_0, freq='D').days.values
        
        species_ensemble.append(model.predict(to_predict = climate.tmean.values, 
                                              doy_series=doy_series))
    
    species_ensemble = np.array(species_ensemble).astype(np.float)
    # apply nan to non predictions
    species_ensemble[species_ensemble==-999]=np.nan
    
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
    species_forecast = species_forecast.chunk({'lat':50,'lon':50})

    if i==0:
        all_species_forecasts = species_forecast
    else:
        all_species_forecasts = xr.merge([all_species_forecasts,species_forecast])

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

all_species_forecasts['note']=provenance_note

forecast_filename = config['phenology_forecast_folder']+'phenology_forecast_'+str(today)+'.nc'

all_species_forecasts = all_species_forecasts.chunk({'lat':50,'lon':50})
all_species_forecasts.to_netcdf(forecast_filename, encoding={'doy_prediction':{'zlib':True},
                                                             'doy_sd':{'zlib':True}})
