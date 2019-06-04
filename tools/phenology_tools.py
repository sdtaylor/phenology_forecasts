import pandas as pd
import numpy as np
import xarray as xr
from pyPhenology import utils

def predict_phenology_from_climate(model, climate_forecast_files, post_process, 
                          doy_0, species_range=None, n_jobs=1):
    """Predict a phenology model over climate ensemble
    
    model
        A saved model file, or pyPhenology object
    
    climate_forecasts
        A list of xarray objects. each one a climate forecast
        
    post_process
        How to deal with multiple forecasts and/or bootstraps
        'automated': for the automated website forecasts. Returns
                    a tuple (prediction_doy, prediction_sd) each with shape
                    (lat, lon)
        'hindcast': for hindcasting where I want all the bootstrap + 
                    climate ensembles. returns a single array
                    prediction_doy of shape (n_ensemble, n_bootstrap, lat, lon)
    
    doy_0
        A timestamp for doy_0, usually Jan 1 of the year in question
        
    species_range
        xarray object from the species range code representing 1 species
        
    returns
        numpy array of (a,b,lat,lon)
    """
    if post_process not in ['automated','hindcast']:
        raise ValueError('Uknown post-processing routine: ' + str(post_process))
    
    # If not a pre-fitted model then assume it's a saved file to load
    try:
        model.get_params()
    except:
        model = utils.load_saved_model(model)
    
    
    species_ensemble = []
    for climate_file in climate_forecast_files:
        climate = xr.open_dataset(climate_file)
        doy_series =  pd.TimedeltaIndex(climate.time.values - doy_0, freq='D').days.values
        
        # When using a bootstrap model in hindcasting we want *all*
        # the predictions. Otherwise just the mean will do
        if type(model).__name__ == 'BootstrapModel' and post_process=='hindcast':
            species_ensemble.append(model.predict(predictors={'temperature': climate.tmean.values,
                                                              'doy_series' : doy_series},
                                                  aggregation='none',
                                                  n_jobs=n_jobs))
        else:
            species_ensemble.append(model.predict(predictors={'temperature': climate.tmean.values,
                                                              'doy_series' : doy_series},
                                                  n_jobs=n_jobs))
    
    species_ensemble = np.array(species_ensemble).astype(np.float)
    # apply nan to non predictions
    species_ensemble[species_ensemble==999]=np.nan
    
    # Keep only values in the range
    if species_range:
        species_ensemble[:,~species_range.range.values]=np.nan
    
    if post_process == 'automated':
    
        prediction_doy = np.nanmean(species_ensemble, axis=0)
        prediction_sd = np.nanstd(species_ensemble, axis=0)
        
        # extend the axis by 2 to match the xarray creation
        prediction_doy= np.expand_dims(prediction_doy, axis=0)
        prediction_doy= np.expand_dims(prediction_doy, axis=0)
        prediction_sd = np.expand_dims(prediction_sd, axis=0)
        prediction_sd = np.expand_dims(prediction_sd, axis=0)
    
        return prediction_doy, prediction_sd
        
    elif post_process == 'hindcast':
        return species_ensemble

