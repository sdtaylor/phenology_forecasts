#import xarray as xr
from ftplib import FTP
import datetime


class cfs_ftp_info:
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
            dir_listing = self.con.nlst(dir_to_list)
            last_entry = self._last_element(dir_listing)
            dir_to_list+='/'+last_entry
        return last_entry
    
    def _string_to_date(self, s):
        return datetime.datetime.strptime(s, '%Y%m%d%H')
    
    def _date_to_string(self,d):
        return d.strftime('%Y%m%d%H')
    
    def _build_full_path(self, forecast_time):
        year = forecast_time.strftime('%Y')
        month= forecast_time.strftime('%m')
        day  = forecast_time.strftime('%d')
        hour = forecast_time.strftime('%H')
        
        return self.base_dir+'/'+year+'/'+year+month+'/'+year+month+day+'/'+year+month+day+hour+'/'
        
    def last_n_forecasts(self, n = 10):
        all_forecasts = []
        latest_forecast_str = self.latest_forecast_timestamp()
        latest_forecast_time = self._string_to_date(latest_forecast_str)
        
        all_forecasts.append({'forecast_time':latest_forecast_str,
                              'forecst_path':self._build_full_path(latest_forecast_time)})
        
        six_hours = datetime.timedelta(hours=6)
        for i in range(n-1):
            latest_forecast_time-=six_hours
            latest_forecast_str = self._date_to_string(latest_forecast_time)
            
            all_forecasts.append({'forecast_time':latest_forecast_str,
                                  'forecast_path':self.build_full_path(latest_forecast_time)})
        return all_forecasts
    

class prism_ftp_info:
    def __init__(self, host='prism.nacse.org', base_dir='daily/tmean', 
                 user='anonymous',passwd='abc123'):
        self.host=host
        self.base_dir=base_dir
        self.con = FTP(host=self.host, user=user, passwd=passwd)
        self._folder_file_lists={}
        
    #Ensure that each folder is only queried once
    def _get_folder_listing(self, folder):
        if folder in self._folder_file_lists:
            return self._folder_file_lists[folder]
        else:
            dir_listing = self.con.nlst(folder)
            self._folder_file_lists[folder]=dir_listing
            return dir_listing

    # The folder a daily date should be in
    def _get_date_folder(self, date):
        year = date.strftime('%Y')
        return self.base_dir+'/'+year+'/'
    
    def _build_prism_filename(self, date):
        pass
    
    def _get_date_filename(self, date):
        folder_to_check = self._get_date_folder(date)
        folder_contents = self._get_folder_listing(folder_to_check)
        date_str = date.strftime('%Y%m%d')
        matching = [filename for filename in folder_contents if date_str in filename]
        assert len(matching)<=1, 'More than 1 matching filename in folder'
        
        if len(matching)==0:
            return None
        else:
            return matching[0]
            
    # returns stable,provisional,early, or none
    def get_date_status(self, date):
        date_filename = self._get_date_filename(date)
        if date_filename is not None:
            status = date_filename.split(sep='_')[-4]
            return status
        else:
            return None
        

#ftp = ftp_info(host = 'nomads.ncdc.noaa.gov',
#               base_dir = 'modeldata/cfsv2_forecast_ts_9mon/')
ftp = prism_ftp_info()