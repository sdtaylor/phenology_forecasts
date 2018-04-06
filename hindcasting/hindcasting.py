import xarray as xr
import pandas as pd
import numpy as np
from tools import tools
from tools.phenology_tools import predict_phenology_from_climate
import os
import datetime
import time
import glob
from automated_forecasting.climate import cfs_forecasts
from pyPhenology import utils

config = tools.load_config()

class hindcast_worker:
    def __init__(self):
        pass

    def get_failed_job_result(self, job_details):
        # Job details is a python date object from hindcast_boss.get_next_job
        return job_details

    def setup(self):
        print('seting things up')
        pass
    
    def run_job(self, job_details):
        climate_forecast_folder = job_details['tmp_folder']+'climate_forecasts'
        tools.make_folder(climate_forecast_folder)
        
        # Make the observed climate only up to the prior day of the forecast date
        current_season_observed = xr.open_dataset(config['current_season_observed_file'])
        observed_days_to_keep = current_season_observed.time < np.datetime64(job_details['date'])
        current_season_observed = current_season_observed.sel(time=observed_days_to_keep)
        
        # Download and process climate forecasts
        cfs_forecasts.get_forecasts_from_date(forecast_date=job_details['date'],
                                              destination_folder=climate_forecast_folder,
                                              lead_time = 36,
                                              forecast_ensemble_size=5,
                                              current_season_observed=current_season_observed)
        
        # Run the phenology models
        
        print('running job')
        return job_details
        
class hindcast_boss:
    def __init__(self):
        pass
    
    def setup(self):
        begin_date = tools.string_to_date('20180101', h=False)
        end_date = tools.string_to_date('20180315', h=False)

        #  Run a hindcast every 4 days
        date_range=pd.date_range(begin_date, end_date, freq='4D').to_pydatetime()
        
        job_list=[]
        for i, d in enumerate(date_range):
            job_list.append({'date':d,
                             'current_season_observed_file':'/home/data/',
                             'tmp_folder':'/tmp/shawn/'+str(i)}+'/')
    
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
    run_MPI(hindcast_boss, hindcast_worker)