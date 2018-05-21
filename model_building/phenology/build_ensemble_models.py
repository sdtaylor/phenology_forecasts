import pyPhenology
import pandas as pd
import numpy as np
from tools import tools
import uuid
import time
import datetime

config = tools.load_config()

today = datetime.datetime.today().date()

divider='#'*90

##############################


def build_phenology_model(species_info):
    temperature_obs = pd.read_csv(config['phenology_observations_temperature_file'])

    species_name=species_info['species']
    phenophase=species_info['Phenophase_ID']
    
    print(divider)
    print('Finding best model for {s} {p}'.format(s=species_name, p=phenophase))
    
    try:
        species_obs = pd.read_csv(config['phenology_observations_folder']+species_info['observation_file'])
        # Only keep temp data for sites for this species
        temperature_obs = temperature_obs[temperature_obs.site_id.isin(species_obs.site_id)]
        species_obs, temperature_obs = pyPhenology.utils.check_data(species_obs, temperature_obs)
    except:
        return({})

    # Different ensemble for fall sensesence model
    if phenophase==498:
        m1 = pyPhenology.models.Linear(parameters={'time_start':(180,300), 'time_length':(10,90)})
        m2 = pyPhenology.models.FallCooling()
        ensemble_models = [m1,m2]
        
        model_note = """Weighted ensemble using stacking,40 iterations, and 3 models (FallCooling, Naive, and Linear w/ fall time estimated."""

    else: 
        m1 = pyPhenology.models.Alternating()
        m2 = pyPhenology.models.ThermalTime()
        m3 = pyPhenology.models.Uniforc()
        m4 = pyPhenology.models.Linear(parameters={'time_start':(-30,60), 'time_length':(1,120)})
        ensemble_models = [m1,m2,m3,m4]
        
        model_note = """Weighted ensemble using stacking,40 iterations, and 4 models (Thermaltime, Uniforc, Alternating, Linear w/ springtime estimated."""

    
    model = pyPhenology.models.WeightedEnsemble(core_models=ensemble_models)
    
    model.fit(species_obs, temperature_obs, iterations=100)
    
    model_hash = str(uuid.uuid1())
    model_filename = '{s}_{p}_{h}.json'.format(s=species_info['species'].replace(' ','_'),
                                               p=species_info['Phenophase_ID'],
                                               h=model_hash)
    
    model.save_params(config['phenology_model_folder']+model_filename)
    
    ###################
    # Entry for model metadata
    
    model_metadata ={'species':species_name,
                     'Phenophase_ID':phenophase,
                     'base_model':'WeightedEnsemble',
                     'forecast_version':3,
                     'model_file':model_filename,
                     'build_date':str(today),
                     'n_observations':len(species_obs),
                     'percent_test':0.2,
                     'note':model_note}
    
    return model_metadata

if __name__ == '__main__':
    ######################################################
    # Setup dask cluster
    ######################################################
    from dask_jobqueue import SLURMCluster
    from dask.distributed import Client
    from time import sleep

    num_hipergator_workers=120
    cluster = SLURMCluster(processes=1,queue='hpg2-compute', threads=1, memory='4GB', walltime='96:00:00',
                       death_timeout=600, local_directory='/tmp/')

    print('Starting up workers')
    workers = cluster.start_workers(num_hipergator_workers)

    dask_client = Client(cluster)

    wait_time=0
    while len(dask_client.scheduler_info()['workers']) < num_hipergator_workers/2:
        print('waiting on workers: {s} sec. so far'.format(s=wait_time))
        sleep(10)
        wait_time+=10
    
        # If 5 minutes goes by try adding them again
        if wait_time > 300:
            workers.extend(cluster.start_workers(1))

    print('Most workers accounted for')


    ##################################################
    # Main

    species_info = pd.read_csv(config['species_list_file'])
        
    job_list=species_info.to_dict('records')

    # job_list will be iterated over, with each one being submitted
    # to a different worker and run with build_phenology_model
    #
    # remote_jobs is a pointer to those, to give the status, job location, etc.
    # as well as the results when the jobs are finished
    remote_jobs = dask_client.map(build_phenology_model, job_list)

    # This collects all the job results (a list of returned values from build_phenology_model)
    # it blocks until all jobs have completed
    model_metadata = dask_client.gather(remote_jobs)

    # Write out the metadata
    tools.append_csv(pd.DataFrame(model_metadata), config['phenology_model_metadata_file'])

