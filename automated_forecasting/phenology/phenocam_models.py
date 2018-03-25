import xarray as xr
import pandas as pd
import numpy as np
from tools import tools
import datetime
import time
import glob
from pyPhenology import utils


# Model parameters from Eli Melaas
phenocam_models = [{'base_model':'Alternating',
                    'nickname' : 'AT_Jan1_5C',
                    'parameters':{'a': 0.85,
                                  'b': 760.32,
                                  'c': -0.017}},
                   {'base_model':'ThermalTime',
                    'nickname' : 'TT_Jan1_5C',
                    'parameters':{'t1': 1,
                                  'T' : 5,
                                  'F' : 212.21}},
                   {'base_model':'ThermalTime',
                    'nickname' : 'TT',
                    'parameters':{'t1': 73,
                                  'T' : -3.17,
                                  'F' : 487.95}}]

# the  m1 model, not yet implimented
#  {'base_model':'ThermalTime',
#   'nickname': 'M1s_Jan1_5C',
#   'parameters':{'t1': 1,
#                 'T' : 5,
#                 'F' : 1512.74,
#                 'exp':7.69}


def run():
    divider='#'*90
    
    config = tools.load_config()
    
    today = datetime.datetime.today().date()
    
    land_mask = xr.open_dataset(config['mask_file'])
    
    print(divider)
    print('Applying phenocam phenology models - ' + str(today))
    
    doy_0 = np.datetime64('2018-01-01')
    
    current_climate_forecast_files = glob.glob(config['current_forecast_folder']+'*.nc')
    
    print(str(len(current_climate_forecast_files)) + ' current climate forecast files: \n' + str(current_climate_forecast_files))
    
    print(divider)
    
    # Load the climate forecasts
    
    current_climate_forecasts = [xr.open_dataset(f) for f in current_climate_forecast_files]
    
    for i, forecast_info in enumerate(phenocam_models):
        model_nickname = forecast_info['nickname']
        model_parameters = forecast_info['parameters']
        base_model_name = forecast_info['base_model']
        Model = utils.load_model(base_model_name)
        model = Model(parameters=model_parameters)
        
        print('attempting phenocam model ' + model_nickname)
        #TODO: use tools.phenology_tools stuff here
        ensemble = []
        for climate in current_climate_forecasts:
            doy_series =  pd.TimedeltaIndex(climate.time.values - doy_0, freq='D').days.values
            
            ensemble.append(model.predict(to_predict = climate.tmean.values, 
                                                  doy_series=doy_series))
        
        ensemble = np.array(ensemble).astype(np.float)
        # apply nan to non predictions
        ensemble[ensemble==999]=np.nan
        
        prediction = np.mean(ensemble, axis=0)
        prediction_sd = np.std(ensemble, axis=0)
        
        # extend the axis by 1 to match the xarray creation
        prediction = np.expand_dims(prediction, axis=0)
        prediction_sd = np.expand_dims(prediction_sd, axis=0)
        
        forecast = xr.Dataset(data_vars = {'doy_prediction':(('model', 'lat','lon'), prediction),
                                                   'doy_sd':(('model', 'lat','lon'), prediction_sd)},
                                      coords = {'model':[model_nickname],
                                                'lat':land_mask.lat, 'lon':land_mask.lon})
        forecast = forecast.chunk({'lat':50,'lon':50})
    
        if i==0:
            phenocam_forecasts = forecast
        else:
            phenocam_forecasts = xr.merge([phenocam_forecasts,forecast])
    
    print(divider)
    print('phenocam phenology forecast final processing')
    
    current_season = tools.current_growing_season(config)
    
    provenance_note = \
    """Forecasts for plant phenology of select species flowering and/or leaf out
    times for the {s} season. Made on {t} from NOAA CFSv2
    forecasts downscaled using PRISM climate data.
    Phenocam models built by Eli Melaas. 
    """.format(s=current_season, t=today)
    
    phenocam_forecasts.attrs['note']=provenance_note
    phenocam_forecasts.attrs['issue_date']=str(today)
    phenocam_forecasts.attrs['crs']='+init=epsg:4269'
    
    forecast_filename = config['phenology_forecast_folder']+'phenocam_phenology_forecast_'+str(today)+'.nc'
    
    phenocam_forecasts = phenocam_forecasts.chunk({'lat':50,'lon':50})
    phenocam_forecasts.to_netcdf(forecast_filename, encoding={'doy_prediction':{'zlib':True,
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
