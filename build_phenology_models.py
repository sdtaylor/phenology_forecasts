import pyPhenology
import pandas as pd
import numpy as np
from tools import tools
import uuid
import time
import datetime
from pySimpleMPI.framework import run_MPI


config = tools.load_config()
percent_test = 0.2
datetime.datetime.today().date()
potential_base_models = ['ThermalTime','Alternating', 'Uniforc']
divider='#'*90

class model_finder_worker:
    def __init__(self):
        pass

    def setup(self):
        self.temperature_obs = pd.read_csv(config['phenology_observations_temperature_file'])
        self.today = datetime.datetime.today().date()
        print('seting things up')
    
    def get_failed_job_result(self, species_info):
        return species_info
    
    def run_job(self, species_info):
        
        species_name=species_info['species']
        phenophase=species_info['Phenophase_ID']
        
        print(divider)
        print('Finding best model for {s} {p}'.format(s=species_name, p=phenophase))
        
        species_obs = pd.read_csv(config['phenology_observations_folder']+species_info['observation_file'])
        species_obs, temperature_obs = pyPhenology.utils.check_data(species_obs, self.temperature_obs)
    
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
                                  n_param = len(model._parameters_to_estimate))
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
        model_filename = '{s}_{p}_{h}.csv'.format(s=species_info['species'].replace(' ','_'),
                                                  p=species_info['Phenophase_ID'],
                                                  h=model_hash)
    
        best_base_model.save_params(config['phenology_model_folder']+model_filename)
        
        #######################################################
        # Iterate this species/phenophase forecast version
        try:
            current_version = species_info['current_forecast_version']
        except:
            current_version = 0
        
        current_version+=1
    
        species_info['current_forecast_version']=current_version
        
        #######################################################
        # make entry for this specifc model in model metadata file
        model_note = """Selected the best model via aic from ThermalTime,Alternating and Uniforc."""
    
        model_metadata ={'species':species_info['species'],
                         'Phenophase_ID':species_info['Phenophase_ID'],
                         'base_model':best_base_model_name,
                         'forecast_version':current_version,
                         'model_file':model_filename,
                         'build_date':str(self.today),
                         'n_observations':len(species_obs),
                         'percent_test':percent_test,
                         'note':model_note}
        
           
        return {'info':species_info, 'metadata':model_metadata}
        
class model_finder_boss:
    def __init__(self):
        pass
    
    def setup(self):
        self.species_info = pd.read_csv(config['species_list_file'])
        
        self.job_list=self.species_info.to_dict('records')
        self.updated_species_info = []
        self.model_metadata = []

        self.today = datetime.datetime.today().date()
    
    def set_total_jobs(self):
        self.total_jobs=len(self.job_list)
    
    def jobs_available(self):
        return len(self.job_list)>0
        
    def get_next_job(self):
        return self.job_list.pop()
    
    def process_job_result(self, result):
        self.updated_species_info.append(result['info'])
        self.model_metadata.append(result['metadata'])
    
    def process_failed_job(self, species_info):
        print('Job failed for {s} {p}'.format(s=species_info['species'],
                                              p=species_info['phenophase']))

    def process_all_results(self, all_results):
        tools.update_csv(pd.DataFrame(self.updated_species_info), config['species_list_file'])
        tools.append_csv(pd.DataFrame(self.model_metadata), config['phenology_model_metadata_file'])
        
if __name__ == "__main__":
    run_MPI(model_finder_boss(), model_finder_worker())






