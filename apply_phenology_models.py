import xarray as xr
import pandas as pd
import numpy as np
from tools import tools
import os
import glob
import warnings

from pyPhenology import utils

config = tools.load_config()

doy_0 = np.datetime64('2018-01-01')

current_climate_forecasts = glob.glob(config['current_forecast_folder']+'*.nc')

forecast_metadata = [{'species':'acer rubrum',
                      'phenophase':501,
                      'model':'ThermalTime',
                      'model_file':'acer_rubrum_501_thermaltime.csv'}]

for forecast_info in forecast_metadata:
    species = forecast_info['species']
    phenophase = forecast_info['phenophase']
    model_file = forecast_info['model_file']
    Model = utils.load_model(forecast_info['model'])
    model = Model(parameters=model_file)
    
    # load  model
    # load species mask
    species_ensemble = []
    for f_file in current_climate_forecasts:
        climate = xr.open_dataset(f_file)
        doy_series =  pd.TimedeltaIndex(climate.time.values - doy_0, freq='D').days.values
        
        species_ensemble.append(model.predict(to_predict = climate.tmean.values, 
                                              doy_series=doy_series))
    
    species_ensemble = np.array(species_ensemble)
    prediction = np.mean(species_ensemble, axis=0)
    prediction_sd = np.std(species_ensemble, axis=0)
    