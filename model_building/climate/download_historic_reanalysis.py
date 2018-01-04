import xarray as xr
import pandas as pd
from tools import cfs_tools, tools
import os

####################
# CFS reanalysis
####################

class reanalysis_worker:
    def __init__(self):
        pass
    
    def setup(self):
        self.config = tools.load_config()

        self.land_mask = xr.open_dataset(self.config['mask_file'])

    def run_job(self, reanalysis_details):
        download_url = reanalysis_details['download_url']
        reanalysis_date = reanalysis_details['date']
        local_filename = self.config['tmp_folder'] + os.path.basename(download_url)
        
        download_status = tools.download_file(download_path=download_url, dest_path=local_filename)
    
        # Some issue with the downloading
        if download_status != 0:
            print('Download error for date: '+str(reanalysis_date))
            return_data={'status':1,'date':reanalysis_date}
        else:
            obj = cfs_tools.process_reanalysis(filename=local_filename,
                                               date=reanalysis_date,
                                               target_downscale_array=self.land_mask.to_array()[0])
            year = reanalysis_date.strftime('%Y')
            month= reanalysis_date.strftime('%m')
            processed_filename = self.config['data_folder']+'cfsv2_reanalysis_'+year+month+'.nc'
            time_dims = len(obj.time)
            obj.to_netcdf(processed_filename, encoding={'tmean': {'zlib':True, 
                                                                  'complevel':1, 
                                                                  'chunksizes':(10,10,time_dims)}})
            return_data={'status':0,'date':reanalysis_date}
        
        return return_data

class reanalysis_boss:
    def __init__(self):
        pass
    
    def setup(self):

        self.config = tools.load_config()

        # Collect information on available CFS forecasts
        # TODO: extend this for the full years
        begin_date = tools.string_to_date(str(1995)+'0101', h=False)
        end_date = tools.string_to_date(str(2015)+'1201', h=False)
    
        # CFS reanalysis are monthly
        date_range_monthly = pd.date_range(begin_date, end_date, freq='MS').to_pydatetime()
        
        cfs = cfs_tools.cfs_ftp_info()
    
        self.job_list=[]
        for d in date_range_monthly:
            download_url = cfs.reanalysis_url_from_timestamp(reanalysis_time=d,
                                                             protocal='http')
            self.job_list.append({'download_url':download_url, 'date':d})
        
        self.total_jobs = len(self.job_list)
        
        cfs.close()
    
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

from pySimpleMPI.framework import run_MPI
if __name__ == "__main__":
    run_MPI(reanalysis_boss(), reanalysis_worker())
