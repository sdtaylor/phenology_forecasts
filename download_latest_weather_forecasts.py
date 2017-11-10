import xarray as xr
from ftplib import FTP
import datetime


class ftp_info():
    def __init__(self, host, base_dir, user='anonymous',passwd='abc123'):
        self.host=host
        self.base_dir=base_dir
        self.con = FTP(host=self.host, user=user, passwd=passwd)
        
    def _last_element(self, list_of_entries):
        end_of_all_strings = [entry.split('/')[-1] for entry in list_of_entries]
        end_of_all_strings = sorted(end_of_all_strings)
        return(end_of_all_strings[-1])
        
    def latest_forecast_timestamp(self, dirs_in_tree=4):
        dir_to_list = self.base_dir
        for dirs_in_tree in range(dirs_in_tree):
            print(dir_to_list)
            dir_listing = self.con.nlst(dir_to_list)
            last_entry = self._last_element(dir_listing)
            dir_to_list+='/'+last_entry
        return last_entry
    
    def string_to_date(self, s):
        return datetime.datetime.strptime(s, '%Y%m%d%H')
    
    def date_to_string(self,d):
        return d.strftime('%Y%m%d%H')
    
    def build_full_path(self, forecast_time):
        year = forecast_time.strftime('%Y')
        month= forecast_time.strftime('%m')
        day  = forecast_time.strftime('%d')
        hour = forecast_time.strftime('%H')
        
        return self.base_dir+'/'+year+'/'+year+month+'/'+year+month+day+'/'+year+month+day+hour+'/'
        
    def last_n_forecasts(self, n = 10):
        all_forecasts = []
        latest_forecast_str = self.latest_forecast_timestamp()
        latest_forecast_time = self.string_to_date(latest_forecast_str)
        
        all_forecasts.append({'forecast_time':latest_forecast_str,
                              'forecst_path':self.build_full_path(latest_forecast_time)})
        
        six_hours = datetime.timedelta(hours=6)
        for i in range(n-1):
            latest_forecast_time-=six_hours
            latest_forecast_str = self.date_to_string(latest_forecast_time)
            
            all_forecasts.append({'forecast_time':latest_forecast_str,
                                  'forecst_path':self.build_full_path(latest_forecast_time)})
        return all_forecasts
    

ftp = ftp_info(host = 'nomads.ncdc.noaa.gov',
               base_dir = 'modeldata/cfsv2_forecast_ts_9mon/')
