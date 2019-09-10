import xarray as xr
import pandas as pd
from tools import tools
config = tools.load_config()

# Get the naive values (build from a simple linear average model)
# and the long term average values (from applying ensemble phenology models
# to 20 years of prism data and getting the means)

# The location, species, and phenophases to extract
forecast_data_needed = pd.read_csv(config['data_folder'] + 'evaluation/phenology_2018_observations.csv')
forecast_data_needed = forecast_data_needed[['species','Phenophase_ID','site_id','latitude','longitude']].drop_duplicates()


# The naive values
# built with model_building/phenology/build_naive_phenology_models.py
naive_forecast = xr.open_dataset(config['phenology_naive_model_file'])

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
    


# and the long term averages
# built with model_building/phenology/create_long_term_averages.py
long_term_averages = xr.open_dataset(config['phenology_long_term_averages_file'])

long_term_average_data = []
for row in forecast_data_needed.to_dict('records'):
    if row['Phenophase_ID'] not in long_term_averages.phenophase.values:
        continue
    if row['species'] not in long_term_averages.species.values:
        continue
        
    subset = long_term_averages.sel(lat=row['latitude'], lon=row['longitude'], 
                              method='nearest').sel(species=row['species'], phenophase=row['Phenophase_ID'])
    
    row.update({'doy_prediction':float(subset.doy_mean.values),
                'doy_sd':float(subset.doy_sd.values)})
    long_term_average_data.append(row)
    

naive_model_data = pd.DataFrame(naive_model_data)
long_term_average_data = pd.DataFrame(long_term_average_data)

naive_model_data.to_csv(config['data_folder'] + 'evaluation/naive_model_data_2018.csv', index=False)
long_term_average_data.to_csv(config['data_folder'] + 'evaluation/long_term_average_model_data_2018.csv', index=False)