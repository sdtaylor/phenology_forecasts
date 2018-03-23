from pyPhenology import models
import pandas as pd
import numpy as np
from tools import tools
import xarray as xr
import uuid
import time
import datetime

config = tools.load_config()

all_species_info = pd.read_csv(config['species_list_file'])

predictor_data = pd.read_csv(config['phenology_observations_temperature_file'])
#predictor_data = predictor_data[['site_id','latitude']]

# Land mask for use as reference in spatial stuff
land_mask = xr.open_dataset(config['mask_file'])

# Latitude array of continuous US for use in make spatial naive predictions
lon_size = land_mask.dims['lon']
latitude_array = np.repeat(np.expand_dims(land_mask.lat.values,1), lon_size, axis=1)

range_masks = xr.open_dataset(config['species_range_file'])

today = datetime.datetime.today().date()

all_model_metadata = []

total_species = len(all_species_info)
for i, species_info in enumerate(all_species_info.to_dict('records')):
    species = species_info['species']
    phenophase = species_info['Phenophase_ID']
    
    #####################################################
    # Build the model
    try:
        species_obs = pd.read_csv(config['phenology_observations_folder']+species_info['observation_file'])
    except:
        print('Skipping {s}/{p}, no observation file'.format(s=species, p=phenophase))
        continue
    
    print('Processing {s}/{p}, {i} of {n}'.format(s=species, p=phenophase,
                                                  i=i, n=total_species))
    model = models.BootstrapModel(core_model=models.Naive,
                                       num_bootstraps=50)
    model.fit(species_obs, predictor_data)
    
    ######################################################
    # Save the model parameters
    time.sleep(1)
    model_hash = str(uuid.uuid1())
    model_filename = '{s}_{p}_{h}.json'.format(s=species_info['species'].replace(' ','_'),
                                              p=species_info['Phenophase_ID'],
                                              h=model_hash)

    model.save_params(config['phenology_model_folder']+model_filename)
    
    #######################################################
    # make entry for this specifc model in model metadata file
    # forecast version is -1 cause the models themselves will 
    # never be used in the automated stuff.
    model_note = """Naive model using doy ~ latitude, Variation from bootstrapping"""
    
    all_model_metadata.append({'species':species,
                               'Phenophase_ID':phenophase,
                               'base_model':'Naive',
                               'forecast_version':-1,
                               'model_file':model_filename,
                               'build_date':str(today),
                               'n_observations':len(species_obs),
                               'percent_test':0,
                               'note':model_note})

    
    ########################################################
    # Add to netcfd of naive forecast. But only if there
    # is a range mask available
    
    if species_info['species'] not in range_masks.species.values:
        print('Skipping {s} {p}, no range mask'.format(s=species, p=phenophase))
        continue
    else:
        species_range = range_masks.sel(species=species)
    
    bootstrap_predictions = model.predict(predictors={'latitude':latitude_array},
                                          aggregation='none')
    
    # Keep only values in the range
    bootstrap_predictions[:,~species_range.range.values]=np.nan
    
    prediction = np.mean(bootstrap_predictions, axis=0)
    prediction_sd = np.std(bootstrap_predictions, axis=0)
    
    # extend the axis by 2 to match the xarray creation
    prediction = np.expand_dims(prediction, axis=0)
    prediction = np.expand_dims(prediction, axis=0)
    prediction_sd = np.expand_dims(prediction_sd, axis=0)
    prediction_sd = np.expand_dims(prediction_sd, axis=0)
    
    species_model = xr.Dataset(data_vars = {'doy_prediction':(('species','phenophase', 'lat','lon'), prediction),
                                               'doy_sd':(('species', 'phenophase', 'lat','lon'), prediction_sd)},
                                      coords = {'species':[species], 'phenophase':[phenophase],
                                                'lat':species_range.lat, 'lon':species_range.lon})
    
    if i==0:
        all_naive_models = species_model
    else:
        merge_start_time=time.time()
        all_naive_models = xr.merge([all_naive_models,species_model])
   
# Append model metadata
all_model_metadata = pd.DataFrame(all_model_metadata)
tools.append_csv(all_model_metadata, config['phenology_model_metadata_file'])

# save naive netcdf 
all_naive_models.to_netcdf(config['phenology_naive_model_file'],   encoding={'doy_prediction':{'zlib':True,
                                                                                               'complevel':4, 
                                                                                               'dtype':'int32', 
                                                                                               'scale_factor':0.001,  
                                                                                               '_FillValue': -9999},
                                                                                     'doy_sd':{'zlib':True,
                                                                                               'complevel':4, 
                                                                                               'dtype':'int32', 
                                                                                               'scale_factor':0.001,  
                                                                                               '_FillValue': -9999}})