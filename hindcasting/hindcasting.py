import pandas as pd
import numpy as np
import glob
import datetime
from time import sleep
import time
from tools import tools
from pyPhenology import utils

import hindcast_config
config = tools.load_config()

begin_date = tools.string_to_date(hindcast_config.begin_date, h=False)
end_date   = tools.string_to_date(hindcast_config.end_date, h=False)
date_range=pd.date_range(begin_date, 
                         end_date,
                         freq = hindcast_config.frequency).to_pydatetime()

######
# Species & phenology modeling stuff
hindcast_species = pd.read_csv(config['data_folder']+'species_for_hindcasting.csv')
phenology_model_metadata = pd.read_csv(config['phenology_model_metadata_file'])
forecast_metadata = hindcast_species.merge(phenology_model_metadata, 
                                                           left_on =['species','Phenophase_ID','current_forecast_version'],
                                                           right_on=['species','Phenophase_ID','forecast_version'], 
                                                           how='left')
#######
# Other stuff

doy_0 = np.datetime64(hindcast_config.doy_0)

today = datetime.datetime.today().date()

######################################################
# Setup dask cluster
######################################################
from dask_jobqueue import SLURMCluster
from dask.distributed import Client
from dask import delayed
import dask
cluster = SLURMCluster(processes=1,queue='hpg2-compute', cores=1, memory='10GB', walltime='96:00:00',
                       job_extra=['--qos ewhite-b'],
                       death_timeout=600, local_directory='/tmp/', interface='ib0')

print('Starting up workers')
workers = cluster.start_workers(hindcast_config.num_hipergator_workers)
dask_client = Client(cluster)

wait_time=0
while len(dask_client.scheduler_info()['workers']) < hindcast_config.num_hipergator_workers:
    print('waiting on workers: {s} sec. so far'.format(s=wait_time))
    sleep(10)
    wait_time+=10
    
    # If 5 minutes goes by try adding them again
    if wait_time > 300:
        workers.extend(cluster.start_workers(1))

print('All workers accounted for')
# xr import must be after dask.array, and I think after setup
# up the cluster/client. 
import dask.array as da
import xarray as xr


# For spatial reference
land_mask = xr.open_dataset(config['mask_file'])

#####################################################
# A special wrapper so that pyPheonlogy.model.predict will work inside
# xarray.apply_ufunc, which will automatically parallelize it over the
# dask.distributed cluster.

def apply_phenology_model(climate, model, doy_0):
    doy_series = pd.TimedeltaIndex(climate.time.values - doy_0, freq='D').days.values
    # time is the "core" dimension here, so apply_ufunc moves it to the end. 
    # but pyPhenology models need it at the begining.
    func = lambda x: model.predict(predictors={'temperature':np.moveaxis(x,2,0),'doy_series':doy_series})
    return xr.apply_ufunc(
            func, climate,
            input_core_dims=[['time']],
            dask='parallelized',
            output_dtypes=[float])

######################################################
    
total_dates=len(date_range)
total_species=len(forecast_metadata)
start_time = time.time()
for date_i, hindcast_issue_date in enumerate(date_range):
    
    phenology_hindcast_save_folder = config['phenology_hindcast_folder'] + str(hindcast_issue_date.date()) + '/'
    tools.make_folder(phenology_hindcast_save_folder)
    
    ##################################
    # process the climate forecasts for this date
    climate_forecast_folder = config['data_folder']+'past_climate_forecasts/'+str(hindcast_issue_date.date())+'/'
       
    current_climate_forecast_files = glob.glob(climate_forecast_folder+'*.nc')
      
    # Take a peek at the first one to get the timestep count. needed to 
    # set the chunksize correctly.
    num_timesteps = len(xr.open_dataset(current_climate_forecast_files[0]).time)
    # Load in the just generated climate foreasts. 
    # This is where the dask magic happens. These files are opened on the cluster
    climate_ensemble = [xr.open_dataset(f, chunks={'time':num_timesteps,'lon':200,'lat':200}).persist() for f in current_climate_forecast_files]
    latitude_length = len(land_mask.lat)
    longitude_length = len(land_mask.lon)
    
    ##################
    # Apply phenology models to this past forecast date
    ##################
    num_species_processed=0
    for species_i, forecast_info in enumerate(forecast_metadata.to_dict('records')):
        
        time_elapsed = np.round((time.time() - start_time)/60,0)
        print('Hindcast date {d}/{D}, species {s}/{S}, elapsed time {t} minutes'.format(d = date_i,
                                                                                        D = total_dates,
                                                                                        s = species_i,
                                                                                        S = total_species,
                                                                                        t = time_elapsed))
        
        species = forecast_info['species']
        phenophase = forecast_info['Phenophase_ID']
        model_file = config['phenology_model_folder']+forecast_info['model_file']
        base_model_name = forecast_info['base_model']
        model = utils.load_saved_model(model_file)
    
        #pair down models for testing
        #model.model_list = model.model_list[0:2]
        #model.model_list[0].model_list = model.model_list[0].model_list[0:20]
        #model.model_list[1].model_list = model.model_list[1].model_list[0:20]
        for submodel in model.model_list:
            submodel.model_list = submodel.model_list[0:20]

        # The number of models in the ensemble
        num_pheno_ensembles = len(model.model_list)
        pheno_ensemble_names = [m['parameters'][0]['model_name'] for m in model._get_model_info()['core_models']]
        num_bootstraps = len(model.model_list[0].model_list)
        
        #prediction_array = np.empty((hindcast_config.num_climate_ensemble, num_pheno_ensembles, num_bootstraps, latitude_length, longitude_length))
        #predicts = []
        ensemble_results = []
        for ensemble_model_i, ensemble_model in enumerate(model.model_list):
            #predicts.append([])
            climate_ensemble_results=[]
            for climate_i, climate in enumerate(climate_ensemble):
                
                bootstrap_results = []
                for bootstrap_i, bootstrap_model in enumerate(ensemble_model.model_list):

                    print('pheno-ensemble: {p}, climate-ensemble: {c}, bootstrap: {b}'.format(p=ensemble_model_i, c=climate_i, b=bootstrap_i))
                    # This step get run on the cluster. with only predictions being saved locally on the "head" machine
                    bootstrap_results.append(apply_phenology_model(climate = climate['tmean'], 
                                                                                     model=bootstrap_model,
                                                                                     doy_0=doy_0).persist())
                    # Potentially a more clever/quicker way of doing it, but not working just yet
                    #predicts[-1].append( apply_phenology_model(climate = climate['tmean'], 
                    #                                                                 model=bootstrap_model,
                    #                                                                 doy_0=doy_0).persist())
        
                #bootstrap_results = dask.compute(*bootstrap_results)
                climate_ensemble_results.append(da.stack(bootstrap_results))
                time.sleep(10) # let the dask scheduler catch up
            ensemble_results.append(da.stack(climate_ensemble_results))
        
        prediction_array = da.stack(ensemble_results)
        ensemble_results=[]
        climate_ensemble_results=[]
        # apply nan to non predictions
        #prediction_array[prediction_array==999]=np.nan
        # extend the axis by 2 to include dimensions for species and phenophase
        #prediction_array = np.expand_dims(prediction_array, axis=0)
        #prediction_array = np.expand_dims(prediction_array, axis=0)
        
        #model_weights = model.weights
        #model_weights = np.expand_dims(model_weights, axis=0)
        #model_weights = np.expand_dims(model_weights, axis=0)
        
        print(prediction_array.shape)
        #prediction_array = dask.optimize(prediction_array)[0]
        #prediction_array = prediction_array.persist()
       
        prediction_dataset = xr.Dataset(data_vars = {'prediction':(('phenology_ensemble','climate_ensemble','bootstrap', 'lat','lon'), prediction_array.compute())},
                                          coords = {'bootstrap':range(num_bootstraps),
                                                    'climate_ensemble':range(hindcast_config.num_climate_ensemble), 'phenology_ensemble':pheno_ensemble_names,
                                                    'lat':land_mask.lat, 'lon':land_mask.lon})
        prediction_array=None
        prediction_dataset = prediction_dataset.expand_dims('species', axis=0).assign_coords(species=[species])
        prediction_dataset = prediction_dataset.expand_dims('phenophase', axis=0).assign_coords(species=[phenophase])
        
        #prediction_dataset.attrs['species']=species
        #prediction_dataset.attrs['phenophase']=phenophase
        prediction_dataset.attrs['issue_date']=str(hindcast_issue_date.date())
        prediction_dataset.attrs['model_run_date']=str(today)
        prediction_dataset.attrs['crs']='+init=epsg:4269'
        
        hindcast_filename = phenology_hindcast_save_folder+species.replace(' ','_')+'_'+str(phenophase)+'_hindcast_'+str(hindcast_issue_date.date())+'.nc'
        prediction_dataset.to_netcdf(hindcast_filename)
        prediction_dataset.close()
        #prediction_dataset.to_netcdf(hindcast_filename,encoding={'prediction':{'zlib':True,
        #                                                                           'complevel':4, 
        #                                                                           'dtype':'int32', 
        #                                                                           'scale_factor':0.001,  
        #                                                                           '_FillValue': -9999}} )
        prediction_dataset=None
