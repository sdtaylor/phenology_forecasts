import xarray as xr
import pandas as pd
import glob
from tools import tools
from copy import deepcopy
config = tools.load_config()


# The location, species, and phenophases to extract
forecast_data_needed = pd.read_csv(config['phenology_current_season_observation_file'])
forecast_data_needed = forecast_data_needed[['species','Phenophase_ID','site_id','latitude','longitude']].drop_duplicates()


available_forecast_date_folders = glob.glob(config['phenology_hindcast_folder']+'20*')

forecast_data = []
for forecast_date_folder in available_forecast_date_folders:
    
    forecast_files = glob.glob(forecast_date_folder + '/*.nc')
    
    for forecast_file in forecast_files:
        forecast_obj = xr.open_dataset(forecast_file)   
        forecast_issue_date = forecast_obj.issue_date
        forecast_obj.load()
        print(forecast_issue_date, str(forecast_obj.species.values))
        for row in forecast_data_needed.to_dict('records'):
            if row['Phenophase_ID'] not in forecast_obj.phenophase.values:
                continue
            if row['species'] not in forecast_obj.species.values:
                continue

            subset = forecast_obj.sel(lat=row['latitude'], lon=row['longitude'], 
                                      method='nearest').sel(species=row['species'], phenophase=row['Phenophase_ID'])
            
            for climate_i in subset.climate_ensemble:
                for phenology_i in subset.phenology_ensemble:
                    new_row = deepcopy(row)
                    new_row.update({'prediction':float(subset.sel(climate_ensemble=climate_i,
                                                              phenology_ensemble=phenology_i).prediction.values),
                                'phenology_weight':float(subset.sel(climate_ensemble=climate_i,
                                                              phenology_ensemble=phenology_i).model_weights.values),
                                'phenology_model':str(phenology_i.phenology_ensemble.values),
                                'climate_ensemble':int(climate_i.climate_ensemble.values),
                                'issue_date':forecast_issue_date})
                    forecast_data.append(new_row)
        
        forecast_obj.close()


forecast_data = pd.DataFrame(forecast_data)
forecast_data.to_csv('/home/shawn/data/phenology_forecasting/validation/forecast_data.csv', index=False)
