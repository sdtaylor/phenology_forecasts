import pandas as pd
import numpy as np
import glob
import datetime
from time import sleep
from tools import tools
#from tools.phenology_tools import predict_phenology_from_climate
from automated_forecasting.climate import cfs_forecasts
#from automated_forecasting.phenology import apply_phenology_models
from pyPhenology import utils

config = tools.load_config()


######
# Climate stuff
num_climate_ensemble = 5
climate_lead_time = 36 # This is in weeks
num_hipergator_workers=10

hindcast_begin_date = tools.string_to_date('20180101', h=False)
hindcast_end_date   = tools.string_to_date('20180401', h=False)
#  Run a hindcast every 4 days
date_range=pd.date_range(hindcast_begin_date, hindcast_end_date, freq='4D').to_pydatetime()

current_season_observed_file = config['tmp_folder']+'climate_observations_2018.nc'

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

current_season=2018

doy_0 = np.datetime64('2018-01-01')

today = datetime.datetime.today().date()

######################################################
# Setup dask cluster
######################################################
from dask_jobqueue import SLURMCluster
from dask.distributed import Client
from dask import delayed
cluster = SLURMCluster(processes=1,queue='hpg1-compute', threads=1, memory='4GB', walltime='00:60:00')

print('Starting up workers')
workers = []
for _ in range(num_hipergator_workers):
    workers.extend(cluster.start_workers(1))
    sleep(2)
dask_client = Client(cluster)

wait_time=0
while len(dask_client.scheduler_info()['workers']) < num_hipergator_workers:
    print('waiting on workers: {s} sec. so far'.format(s=wait_time))
    sleep(10)
    wait_time+=10
    
    # If 5 minutes goes by try adding them again
    if wait_time > 600:
        workers.extend(cluster.start_workers(1))

print('All workers accounted for')
# xr import must be after dask.array, and I think after setup
# up the cluster/client. 
import dask.array as da
import xarray as xr


# For spatial reference
land_mask = xr.open_dataset(config['mask_file'])

#####################################################
# I am having issues on the hipergator where these locations
# are missing some, but not all, temperature values. I can't 
# figure out, or reproduce it on serenity. 11 pixels is nothing
# so I'm just going to mark them all NA and move on. 
def hipergator_correction(climate_forecast):
    bad_pixels_axis_1 = np.array([ 47,  51,  68, 128, 139, 143, 213, 238, 372, 411, 440])
    bad_pixels_axis_2 = np.array([ 700,  794,  506, 1220,  595,  626, 1179,  688,  516,  481,  463])
    
    climate_forecast['tmean'][:,bad_pixels_axis_1,bad_pixels_axis_2] = np.nan

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
            output_dtypes=[float]).values

######################################################
for date_i, hindcast_issue_date in enumerate(date_range):
    
    phenology_hindcast_save_folder = config['phenology_hindcast_folder'] + str(hindcast_issue_date.date()) + '/'
    tools.make_folder(phenology_hindcast_save_folder)
    
    ##################################
    # process the climate forecasts for this date
    climate_forecast_folder = config['data_folder']+'hindcasts/past_climate/'+str(date_i)+'/'
    tools.make_folder(climate_forecast_folder)
    # Make the observed climate only up to the prior day of the forecast date
    current_season_observed = xr.open_dataset(current_season_observed_file)
    observed_days_to_keep = current_season_observed.time < np.datetime64(hindcast_issue_date)
    current_season_observed = current_season_observed.sel(time=observed_days_to_keep)
    
    # Download and process climate forecasts
    cfs_forecasts.get_forecasts_from_date(forecast_date=hindcast_issue_date,
                                          destination_folder=climate_forecast_folder,
                                          lead_time = climate_lead_time,
                                          forecast_ensemble_size=num_climate_ensemble,
                                          current_season_observed=current_season_observed)
    
    current_climate_forecast_files = glob.glob(climate_forecast_folder+'*.nc')
    
    # Apply this small fix because I don't know how else to deal with it. 
    for f in current_climate_forecast_files:
        obj = xr.open_dataset(f)
        obj.load()
        hipergator_correction(obj)
        obj.close()
        obj.to_netcdf(f)
    
    num_timesteps = len(obj.time)
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
        species = forecast_info['species']
        phenophase = forecast_info['Phenophase_ID']
        model_file = config['phenology_model_folder']+forecast_info['model_file']
        base_model_name = forecast_info['base_model']
        model = utils.load_saved_model(model_file)
    
        num_bootstraps = len(model.model_list)
        
        prediction_array = np.empty((num_climate_ensemble, num_bootstraps, latitude_length, longitude_length))
        for bootstrap_i, bootstrap_model in enumerate(model.model_list):
            for climate_i, climate in enumerate(climate_ensemble):
                
                # This step get run on the cluster. with only predictions being saved
                prediction_array[climate_i, bootstrap_i]= apply_phenology_model(climate = climate['tmean'], 
                                                                                 model=bootstrap_model,
                                                                                 doy_0=doy_0)
    
        prediction_dataset = xr.Dataset(data_vars = {'prediction':(('climate_ensemble','bootstrap', 'lat','lon'), prediction_array)},
                                          coords = {'climate_ensemble':range(num_climate_ensemble), 'bootstrap':range(num_bootstraps),
                                                  'lat':land_mask.lat, 'lon':land_mask.lon})
    
        prediction_dataset.attrs['species']=species
        prediction_dataset.attrs['phenophase']=phenophase
        prediction_dataset.attrs['issue_date']=str(hindcast_issue_date.date())
        prediction_dataset.attrs['model_run_date']=str(today)
        prediction_dataset.attrs['crs']='+init=epsg:4269'
        
        hindcast_filename = phenology_hindcast_save_folder+species+'_'+str(phenophase)+'_hindcast_'+str(hindcast_issue_date.date())+'.nc'
        prediction_dataset.to_netcdf(hindcast_filename,encoding={'prediction':{'zlib':True,
                                                                                   'complevel':4, 
                                                                                   'dtype':'int32', 
                                                                                   'scale_factor':0.001,  
                                                                                   '_FillValue': -9999}} )