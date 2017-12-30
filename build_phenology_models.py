import pyPhenology
import pandas as pd
import numpy as np
from tools import tools
import os
import uuid
import time
import datetime

config = tools.load_config()
percent_test = 0.2
potential_base_models = ['ThermalTime','Alternating', 'Uniforc']
species_info = pd.read_csv(config['species_list_file'])

today = datetime.datetime.today().date()

temperature_obs = pd.read_csv(config['phenology_observations_temperature_file'])

model_metadata=[]

divider='#'*90

for i in range(len(species_info)):
    species_name=species_info.species[i]
    phenophase=species_info.Phenophase_ID[i]
    
    print(divider)
    print('Finding best model for {s} {p}'.format(s=species_name, p=phenophase))
    
    species_obs = pd.read_csv(config['phenology_observations_folder']+species_info.observation_file[i])
    species_obs, temperature_obs = pyPhenology.utils.check_data(species_obs, temperature_obs)

    testing_obs = species_obs.sample(frac=percent_test, random_state=1, replace=False)
    training_obs = species_obs[~species_obs.index.isin(testing_obs.index)]
    
    best_aic=np.inf
    best_base_model = None
    best_base_model_name = None
        
    for model_name in potential_base_models:
        Model = pyPhenology.utils.load_model(model_name)
        model = Model()
        model.fit(observations=training_obs, temperature=temperature_obs,
                  optimizer_params={'popsize':100,
                                    'maxiter':50000})
        model_aic = tools.aic(obs = testing_obs.doy.values, 
                              pred = model.predict(testing_obs, temperature_obs),
                              n_param = len(model.get_params()))
        if model_aic < best_aic:
            best_base_model = model
            best_base_model_name = model_name
            best_aic = model_aic
        
        print('model {m} got an aic of {a}'.format(m=model_name,a=model_aic))

    print('Chose {m} for {s} {p}'.format(m=best_base_model_name,
                                         s=species_name,
                                         p=phenophase))
    #######################################################
    # Save the best model using a unique identifier
    time.sleep(1)
    model_hash = str(uuid.uuid1())
    model_filename = '{s}_{p}_{h}.csv'.format(s=species_info.species[i].replace(' ','_'),
                                              p=species_info.Phenophase_ID[i],
                                              h=model_hash)

    best_base_model.save_params(config['phenology_model_folder']+model_filename)
    
    #######################################################
    # Iterate this species/phenophase forecast version
    try:
        current_version = species_info.current_forecast_version[i]
    except:
        current_version = 0
    
    current_version+=1

    species_info['current_forecast_version'][i]=current_version
    #######################################################
    # add entry for this specifc model in model metadata file
    model_note = """Selected the best model via aic from ThermalTime,Alternating and Uniforc.
    """
    
    model_metadata.append({'species':species_info.species[i],
                             'Phenophase_ID':species_info.Phenophase_ID[i],
                             'base_model':best_base_model_name,
                             'forecast_version':current_version,
                             'model_file':model_filename,
                             'build_date':str(today),
                             'n_observations':len(species_obs),
                             'percent_test':percent_test,
                             'note':model_note})
    

tools.update_csv(species_info, config['species_list_file'])
tools.append_csv(pd.DataFrame(model_metadata), config['phenology_model_metadata_file'])