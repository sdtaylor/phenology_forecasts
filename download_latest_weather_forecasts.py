#import xarray as xr
from ftplib import FTP
import datetime
import xarray as xr
import numpy as np
import pandas as pd
import yaml
import os
import zipfile
import urllib


class cfs_ftp_info:
    def __init__(self, host='nomads.ncdc.noaa.gov', 
                 base_dir='modeldata/cfsv2_forecast_ts_9mon/',
                 user='anonymous',passwd='abc123'):
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
    
# Ways to query the PRISM ftp server in meaningful and efficient ways
class prism_ftp_info:
    def __init__(self, host='prism.nacse.org', 
                 base_dir='daily/tmean', 
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
            
    def get_download_url(self, date):
        date_filename = self._get_date_filename(date)
        return 'ftp://'+self.host+'/'+date_filename

    # returns stable,provisional,early, or none
    def get_date_status(self, date):
        date_filename = self._get_date_filename(date)
        if date_filename is not None:
            status = date_filename.split(sep='_')[-4]
            return status
        else:
            return None
        
# a single day matching dataset d
# with NA values and status = None
def make_blank_day_like(d):
    pass

def string_to_date(s, hour=False):
    if hour:
        return datetime.datetime.strptime(s, '%Y%m%d%H')
    else:
        return datetime.datetime.strptime(s, '%Y%m%d')

def current_growing_season():
    today = datetime.datetime.today()
    year = today.strftime('%Y')
    cutoff = datetime.datetime.strptime(year+'1101', '%Y%m%d')
    if today >  cutoff:
        year = str(int(year) + 1)
    return year

def round_to_current_day(t):
    return t - datetime.timedelta(hours=t.hour, 
                                  minutes=t.minute, 
                                  seconds=t.second, 
                                  microseconds=t.microsecond)

def cleanup_tmp_folder():
    for f in os.listdir(config['tmp_folder']):
        os.remove(config['tmp_folder']+f)

def prism_to_xarray(bil_filename, varname, date, status, mask_value=-9999):
    bil = xr.open_rasterio(bil_filename)
    lon, lat = bil.x.values, bil.y.values
    data=bil.values
    data[data==mask_value]=np.nan
    
    xr_dataset = xr.Dataset(data_vars = {varname: (('time','lat','lon'), data),
                                         'status':(('time'), [status])},
                            coords =    {'time':[date],'lat':lat, 'lon':lon},
                            attrs =     {'crs':bil.crs,
                                         'units':'C'})

    return xr_dataset

def download_day(date, varname, status):
    pass

# PRISM file status are stable > provisional > early
def newer_file_available(current_status, available_status):
    if current_status == available_status:
        return False
    elif current_status=='stable':
        return False
    elif current_status=='provisional' and available_status=='stable':
        return True
    elif current_status=='early' and available_status in ['provisional','stable']:
        return True
    elif current_status=='None':
        pass
    else:
        raise Exception('status comparison uknown: '+current_status+' , '+available_status)

if __name__=='__main__':
    with open('config.yaml', 'r') as f:
        config = yaml.load(f)
    data_dir = config['data_folder']
    current_season=current_growing_season()
    observed_weather_file = data_dir+current_season+'_observed_weather.nc'
    
    if os.path.isfile(observed_weather_file):
        observed_weather = xr.open_dataset(observed_weather_file)
    else:
        print('observed weather file not found')
    
    today = round_to_current_day(datetime.datetime.today())
    yesterday = today - datetime.timedelta(days=1)
    
    # The last entry in this seasons observed weather
    latest_observed_day = observed_weather.time.values[-1]
    
    prism_days_to_add = pd.date_range(latest_observed_day, np.datetime64(yesterday), closed='right')
    
    prism = prism_ftp_info()
    
    for day in prism_days_to_add:
        day = day.to_pydatetime()
        day_status = prism.get_date_status(day)
        if day_status is not None:
            download_url = prism.get_download_url(day)
            dest_path  = config['tmp_folder']+os.path.basename(download_url)
            urllib.request.urlretrieve(download_url, dest_path)
            z = zipfile.ZipFile(dest_path, 'r')
            z.extractall(path = config['tmp_folder'])
            z.close()
            bil_filename = dest_path.split('.')[0]+'.bil'
            day_xr = prism_to_xarray(bil_filename, varname='tmean', date=day, status=day_status)

            observed_weather = observed_weather.combine_first(day_xr)
            
        else:
            pass
            # make a blank array for this day with status None
            
    for day in observed_weather.time.values:
        current_status = observed_weather.sel(time=day).status.values.tolist()
        ftp_status = prism.get_date_status(pd.Timestamp(day).to_pydatetime())
        if newer_file_available(current_status, ftp_status):
            print('file_to_update')
    # Iterate thru the weather xarray again and attempt to update
    # anything that has changed status
    
    cleanup_tmp_folder()












