# This is for download large amounts of historic forecasts and observations
# for making the downscaling models. By large I mean like 20 years

import pandas as pd
import yaml
from tools import prism_tools, tools
import xarray as xr


###################
# Download historic PRISM data and convert to netcdf
##################

class prism_download_worker:
    def __init__(self):
        pass

    def setup(self):
        with open('config.yaml', 'r') as f:
            self.config = yaml.load(f)

        self.output_folder = self.config['historic_observations_folder']

    def run_job(self, job_details):
        prism_date = job_details['date']
        download_url = job_details['download_url']
        day_status   = job_details['day_status']
        varname      = job_details['varname']
    
        # download 
        try:
            prism_xarray = prism_tools.download_and_process_day(download_url=download_url,
                                                                varname=varname,
                                                                date=prism_date,
                                                                status=day_status)
            year = prism_date.strftime('%Y')
            month= prism_date.strftime('%m')
            day  = prism_date.strftime('%d')
            processed_filename = self.output_folder+'prism_'+varname+'_'+year+month+day+'.nc'
            
            prism_xarray.to_netcdf(path=processed_filename)
            return_data={'status':0,'date':prism_date}
        except:
            return_data={'status':1,'date':prism_date}
        
        return return_data

class prism_download_boss:
    def __init__(self):
        pass

    def setup(self):
        with open('config.yaml', 'r') as f:
            self.config = yaml.load(f)

        self.output_folder = self.config['data_folder'] + 'historic_observations/'
        
        begin_date = tools.string_to_date(str(self.config['historic_years_begin'])+'0101', h=False)
        end_date = tools.string_to_date(str(self.config['historic_years_end'])+'1231', h=False)

        prism = prism_tools.prism_ftp_info()

        date_range_daily = pd.date_range(begin_date, end_date, freq='1D').to_pydatetime()

        # All dates for PRISM should be available, but check just to make sure
        date_range_daily = [d for d in date_range_daily if prism.date_available(d)]

        self.job_list=[]

        
        for i, d in enumerate(date_range_daily):
            url = prism.get_download_url(d)
            day_status = prism.get_date_status(d)
            self.job_list.append({'date':d,
                                  'download_url':url,
                                  'day_status':day_status,
                                  'varname':'tmean'})
    
        self.total_jobs = len(self.job_list)

        prism.close()

    def jobs_available(self):
        return len(self.job_list)>0

    def get_next_job(self):
        return self.job_list.pop()

    def process_job_result(self, job_result):
        pass

    def process_all_results(self, all_results):
        for r in all_results:
            if r['status']!=0:
                print('failed: ' + str(r['date']))

        tools.cleanup_tmp_folder(self.config['tmp_folder'])

###################
# Compile prism daily data into yearly files
##################

class prism_compile_years_worker:
    def __init__(self):
        pass

    def setup(self):
        with open('config.yaml', 'r') as f:
            self.config = yaml.load(f)

    def run_job(self, job_details):
        year = job_details['year']

        try:
            search_path = self.config['historic_observations_folder']+'prism_tmean_'+str(year)+'*'
            this_year_observations = xr.open_mfdataset(search_path)
            year_filename = self.config['historic_observations_folder'] + 'yearly/'+'prism_tmean_'+str(year)+'.nc'
    
            time_dims = len(this_year_observations.time)
            this_year_observations.to_netcdf(year_filename, encoding={'tmean':{'zlib':True, 
                                                                               'complevel':1, 
                                                                               'chunksizes':(10,10,time_dims)}})
            return_status={'status':0, 'year':year}
        except:
            return_status={'status':1, 'year':year}
        
        return return_status
    
class prism_compile_years_boss:
    def __init__(self):
        pass

    def setup(self):
        with open('config.yaml', 'r') as f:
            self.config = yaml.load(f)
        
        begin_year = self.config['historic_years_begin']
        end_year =   self.config['historic_years_end']
        
        self.job_list = [{'year':year} for year in range(begin_year, end_year+1)]
        self.total_jobs=len(self.job_list)

    def jobs_available(self):
        return len(self.job_list)>0

    def get_next_job(self):
        return self.job_list.pop()

    def process_job_result(self, job_result):
        pass

    def process_all_results(self, all_results):
        for r in all_results:
            if r['status']!=0:
                print('failed: ' + str(r['year']))

        tools.cleanup_tmp_folder(self.config['tmp_folder'])
from pySimpleMPI.framework import run_MPI
if __name__ == "__main__":
    run_MPI(prism_download_boss(), prism_download_worker())
    run_MPI(prism_compile_years_boss(), prism_compile_years_worker())
