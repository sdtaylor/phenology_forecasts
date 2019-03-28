import xarray as xr
import pandas as pd
import glob
from tools import tools
from copy import deepcopy
config = tools.load_config()


# The location, species, and phenophases to extract
forecast_data_needed = pd.read_csv(config['data_folder'] + 'evaluation/phenology_2019_observations.csv')
forecast_data_needed = forecast_data_needed[['species','Phenophase_ID','site_id','latitude','longitude']].drop_duplicates()


available_forecasts = glob.glob(config['phenology_forecast_folder']+'*.nc')

forecast_data = []
for forecast_file in available_forecasts:
    forecast_obj = xr.open_dataset(forecast_file)   
    forecast_issue_date = forecast_obj.issue_date
    forecast_obj.load()
    print(forecast_issue_date)
    for row in forecast_data_needed.to_dict('records'):
        if row['Phenophase_ID'] not in forecast_obj.phenophase.values:
            continue
        if row['species'] not in forecast_obj.species.values:
            continue

        subset = forecast_obj.sel(lat=row['latitude'], lon=row['longitude'], 
                                  method='nearest').sel(species=row['species'], phenophase=row['Phenophase_ID'])
        
        new_row = deepcopy(row)
        new_row.update({'doy_prediction':float(subset.doy_prediction.values),
                        'doy_sd':float(subset.doy_sd.values),
                        'issue_date':forecast_issue_date})
        forecast_data.append(new_row)
    
    forecast_obj.close()


# Don't forget naive forecasts
naive_forecast = xr.open_dataset('/home/shawn/data/phenology_forecasting/phenology_naive_models.nc')

naive_model_data = []
for row in forecast_data_needed.to_dict('records'):
    if row['Phenophase_ID'] not in naive_forecast.phenophase.values:
        continue
    if row['species'] not in naive_forecast.species.values:
        continue
        
        
    subset = naive_forecast.sel(lat=row['latitude'], lon=row['longitude'], 
                              method='nearest').sel(species=row['species'], phenophase=row['Phenophase_ID'])
    
    row.update({'doy_prediction':float(subset.doy_prediction.values),
                'doy_sd':float(subset.doy_sd.values)})
    naive_model_data.append(row)
    
forecast_data = pd.DataFrame(forecast_data)
naive_model_data = pd.DataFrame(naive_model_data)

forecast_data.to_csv('/home/shawn/data/phenology_forecasting/evaluation/forecast_data_2019.csv', index=False)
naive_model_data.to_csv('/home/shawn/data/phenology_forecasting/evaluation/naive_model_data.csv', index=False)
