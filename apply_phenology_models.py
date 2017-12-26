import xarray as xr
import pandas as pd
import numpy as np
from tools import tools
import os
import datetime
import glob

from pyPhenology import utils

config = tools.load_config()

range_masks = xr.open_dataset(config['species_range_file'])

doy_0 = np.datetime64('2018-01-01')

current_climate_forecasts = glob.glob(config['current_forecast_folder']+'*.nc')

forecast_metadata = [{'species':'acer rubrum',
                      'phenophase':501,
                      'model':'ThermalTime',
                      'model_file':'acer_rubrum_501_thermaltime.csv'},
                     {'species':'juniperus virginiana',
                      'phenophase':371,
                      'model':'ThermalTime',
                      'model_file':'juniperus_virginiana_371_thermaltime.csv'}]

all_species_forecasts=[]
for forecast_info in forecast_metadata:
    species = forecast_info['species']
    phenophase = forecast_info['phenophase']
    model_file = forecast_info['model_file']
    Model = utils.load_model(forecast_info['model'])
    model = Model(parameters=model_file)
    
    species_range = range_masks.sel(species=species)

    species_ensemble = []
    for f_file in current_climate_forecasts:
        climate = xr.open_dataset(f_file)
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
                                               'doy_sd':(('species', 'phenophase', 'lat','lon'), prediction)},
                                  coords = {'species':[species], 'phenophase':[phenophase],
                                          'lat':species_range.lat, 'lon':species_range.lon})
    
    all_species_forecasts.append(species_forecast)
    
all_species_forecasts = xr.merge(all_species_forecasts)

current_season = tools.current_growing_season(config)
today = datetime.datetime.today().date()

provenance_note = \
"""Forecasts for plant phenology of select species flowering and/or leaf out
times for the {s} season. Made on {t} from NOAA CFSv2
forecasts downscaled using PRISM climate data.
Plant phenology models made using National Phenology Network data. 
""".format(s=current_season, t=today)

all_species_forecasts['note']=provenance_note

forecast_filename = config['phenology_forecast_folder']+'phenology_forecast_'+str(today)+'.nc'

all_species_forecasts.to_netcdf(forecast_filename, encoding={'doy_prediction':{'zlib':True},
                                                             'doy_sd':{'zlib':True}})