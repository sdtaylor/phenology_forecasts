import xarray as xr
import pandas as pd
import numpy as np
import glob
import datetime
from tools import tools
from tools.phenology_tools import predict_phenology_from_climate
from automated_forecasting.climate import cfs_forecasts
from automated_forecasting.phenology import apply_phenology_models
from pyPhenology import utils
from pySimpleMPI.framework_pythonMP import run_pythonMP

config = tools.load_config()

divider='#'*90

doy_0 = np.datetime64('2018-01-01')

num_climate_ensemble = 5

hindcast_begin_date = tools.string_to_date('20180101', h=False)
hindcast_end_date   = tools.string_to_date('20180115', h=False)

hindcast_species = pd.read_csv(config['data_folder']+'species_for_hindcasting.csv')[1:3]

current_season_observed_file = config['tmp_folder']+'climate_observations_2018.nc'

current_season=2018

today = datetime.datetime.today().date()

#######################################################

class hindcast_worker:
    def __init__(self):
        pass

    def get_failed_job_result(self, job_details):
        # Job details is a python date object from hindcast_boss.get_next_job
        return job_details

    def setup(self):
        print('seting things up')
        species_list = hindcast_species
        phenology_model_metadata = pd.read_csv(config['phenology_model_metadata_file'])
    
        self.forecast_metadata = species_list.merge(phenology_model_metadata, 
                                                    left_on =['species','Phenophase_ID','current_forecast_version'],
                                                    right_on=['species','Phenophase_ID','forecast_version'], 
                                                    how='left')
        self.range_masks = xr.open_dataset(config['species_range_file'])
    
    def run_job(self, job_details):
        print('running job: '+str(job_details['date']))
        climate_forecast_folder = job_details['tmp_folder']+'climate_forecasts/'
        tools.make_folder(climate_forecast_folder)
        
        # Make the observed climate only up to the prior day of the forecast date
        current_season_observed = xr.open_dataset(job_details['current_season_observed_file'])
        observed_days_to_keep = current_season_observed.time < np.datetime64(job_details['date'])
        current_season_observed = current_season_observed.sel(time=observed_days_to_keep)
        
        # Download and process climate forecasts
        cfs_forecasts.get_forecasts_from_date(forecast_date=job_details['date'],
                                              destination_folder=climate_forecast_folder,
                                              lead_time = 36,
                                              forecast_ensemble_size=num_climate_ensemble,
                                              current_season_observed=current_season_observed)
        
        current_climate_forecast_files = glob.glob(climate_forecast_folder+'*.nc')

        
        # Run the phenology models
        num_species_processed=0
        for i, forecast_info in enumerate(self.forecast_metadata.to_dict('records')):
            species = forecast_info['species']
            phenophase = forecast_info['Phenophase_ID']
            model_file = config['phenology_model_folder']+forecast_info['model_file']
            base_model_name = forecast_info['base_model']
            model = utils.load_saved_model(model_file)

            print('Apply model for {s} {p}'.format(s=species, p=phenophase))
            print('forecast attempt {i} of {n} potential species. {n2} processed succesfully so far.'.format(i=i, n=len(self.forecast_metadata), n2=num_species_processed))

            prediction = predict_phenology_from_climate(model,
                                                        current_climate_forecast_files,
                                                        post_process='hindcast',
                                                        doy_0=doy_0,
                                                        species_range=None)
            
            # extend the array by 2 for species and phenophase axis
            prediction = np.expand_dims(prediction, axis=0)
            prediction = np.expand_dims(prediction, axis=0)

            num_bootstraps = len(model.get_params())
            
            species_forecast = xr.Dataset(data_vars = {'prediction':(('species','phenophase','climate_ensemble','bootstrap', 'lat','lon'), prediction)},
                                          coords = {'species':[species], 'phenophase':[phenophase],
                                                    'climate_ensemble':range(num_climate_ensemble), 'bootstrap':range(num_bootstraps),
                                                  'lat':self.range_masks.lat, 'lon':self.range_masks.lon})
        
            if i==0:
                all_species_forecasts = species_forecast
                num_species_processed+=1
            else:
                all_species_forecasts = xr.merge([all_species_forecasts,species_forecast])
                num_species_processed+=1

        # Add forecast details and save
        provenance_note = \
        """This is a phenology hindcast run on {d1} with modelled issue date
        of {d2}
        
        Forecasts for plant phenology of select species flowering and/or leaf out
        times. Made on from NOAA CFSv2 forecasts downscaled using PRISM climate data.
        Plant phenology models made using National Phenology Network data. 
        """.format(d1=today, d2=job_details['date'])
        
        all_species_forecasts.attrs['note']=provenance_note
        all_species_forecasts.attrs['issue_date']=str(job_details['date'])
        all_species_forecasts.attrs['model_run_date']=str(today)
        all_species_forecasts.attrs['crs']='+init=epsg:4269'

        hindcast_filename = config['phenology_hindcast_folder']+'phenology_hindcast_'+str(job_details['date'])+'.nc'
    
        all_species_forecasts = all_species_forecasts.chunk({'lat':50,'lon':50})
        all_species_forecasts.to_netcdf(hindcast_filename, encoding={'prediction':{'zlib':True,
                                                                                   'complevel':4, 
                                                                                   'dtype':'int32', 
                                                                                   'scale_factor':0.001,  
                                                                                   '_FillValue': -9999}})

        return job_details
        
class hindcast_boss:
    def __init__(self):
        pass
    
    def setup(self):
        begin_date = hindcast_begin_date
        end_date   = hindcast_end_date

        #  Run a hindcast every 4 days
        date_range=pd.date_range(begin_date, end_date, freq='4D').to_pydatetime()
        
        self.job_list=[]
        for i, d in enumerate(date_range):
            self.job_list.append({'date':d,
                                  'current_season_observed_file':current_season_observed_file,
                                  'tmp_folder':config['tmp_folder']+'hindcasts/'+str(i)+'/'})
    
    def set_total_jobs(self):
        self.total_jobs = len(self.job_list)

    def jobs_available(self):
        return len(self.job_list)>0
        
    def get_next_job(self):
        return self.job_list.pop()
    
    def process_job_result(self, result):
        pass
    
    def process_failed_job(self, result):
        print('Date failed: ' + str(result))

    def process_all_results(self):
        pass
        
if __name__ == "__main__":
    run_pythonMP(hindcast_boss, hindcast_worker, n_procs=1)
