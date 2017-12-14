import xarray as xr
from ftplib import FTP
import ftplib
import datetime
import numpy as np
import xmap
import yaml
import os
import urllib
import time
from tools import tools

with open('config.yaml', 'r') as f:
    config = yaml.load(f)

class cfs_ftp_info:
    def __init__(self):
        self.host='nomads.ncdc.noaa.gov'
        self.forecast_dirs={'http':{'operational':'modeldata/cfsv2_forecast_ts_9mon/',
                                    'reforecast': 'data/cfsr-rfl-ts9/tmp2m/'},
                            'ftp':{'operational':'modeldata/cfsv2_forecast_ts_9mon/',
                                   'reforecast':'CFSRR/cfsr-rfl-ts9/tmp2m/'}
                            }
        self.reanalysis_dirs={'http':{'operational':'modeldata/cfsv2_analysis_timeseries/',
                                    'pre_2011': 'data/cfsr/'},
                            'ftp':{'operational':'modeldata/cfsv2_analysis_timeseries/',
                                   'pre_2011':'CFSR/HP_time_series/'}
                            }
        #self.forecast_dir='modeldata/cfsv2_forecast_ts_9mon/'
        #self.reforecast_dir='CFSRR/cfsr-rfl-ts9/tmp2m/'
        self.con = FTP(host=self.host, user='anonymous', passwd='abc123')
        self._folder_file_lists={}
    
    def close(self):
        self.con.close()
        
    #Ensure that each folder is only queried once
    def _get_folder_listing(self, folder):
        if folder in self._folder_file_lists:
            return self._folder_file_lists[folder]
        else:
            try:
                dir_listing = self.con.nlst(folder)
            except ftplib.error_temp:
                # Folder not found, aka it's empty
                dir_listing = []
            self._folder_file_lists[folder]=dir_listing
            return dir_listing
        
    def _last_element(self, list_of_entries):
        end_of_all_strings = [entry.split('/')[-1] for entry in list_of_entries]
        end_of_all_strings = sorted(end_of_all_strings)
        return(end_of_all_strings[-1])
        
    def latest_forecast_time_str(self, dirs_in_tree=4):
        # Parse thru the tree structure for the very
        # last element
        dir_to_list = self.forecast_dirs['ftp']['operational']
        for dirs_in_tree in range(dirs_in_tree):
            dir_listing = self.con.nlst(dir_to_list)
            last_entry = self._last_element(dir_listing)
            dir_to_list+='/'+last_entry
        return last_entry
    
    def forecast_available(self, forecast_time):
        if isinstance(forecast_time, str):
            forecast_time = tools.string_to_date(forecast_time, h=True)
        
        # 2011 to present is pretty complete, and also time consuming
        # to check. So of it's in this range just assume it's there
        cutoff_begin = tools.string_to_date('2011040100', h=True)
        cutoff_end   = tools.string_to_date('2017070100', h=True)
        if forecast_time >= cutoff_begin and forecast_time <= cutoff_end:
            return True
        
        forecast_filename = self.forecast_url_from_timestamp(forecast_time, path_type='filename')
        folder = self.forecast_url_from_timestamp(forecast_time, path_type='folder')
        folder_contents = self._get_folder_listing(folder)
        matching = [entry for entry in folder_contents if forecast_filename in entry]
        return len(matching)!=0
    
    # TODO: variable filename to download precip as well
    # forecast download paths look like: 
    # ftp://nomads.ncdc.noaa.gov/modeldata/cfsv2_forecast_ts_9mon/2017/201711/20171111/2017111118/tmp2m.01.2017111118.daily.grb2
    # reforecast paths (prior to 2011) are:
    # ftp://nomads.ncdc.noaa.gov/CFSRR/cfsr-rfl-ts9/tmp2m/200808/tmp2m.2008080418.time.grb2
    # path_types: 
    # folder returns the containing folder but not the protocal or 
    # filename returns only the filename
    # full path returns the full download link
    def forecast_url_from_timestamp(self, forecast_time, path_type='full_path', protocal='ftp'):
        assert path_type in ['full_path','folder','filename'] , 'unknown path type: '+str(path_type)
        assert protocal in ['http','ftp'] , 'unknown protocal: '+str(protocal)
        if isinstance(forecast_time, str):
            forecast_time = tools.string_to_date(forecast_time, h=True)
            
        year = forecast_time.strftime('%Y')
        month= forecast_time.strftime('%m')
        day  = forecast_time.strftime('%d')
        hour = forecast_time.strftime('%H')
        to_return={}
        if int(year) < 2011:
            to_return['filename'] = 'tmp2m.'+tools.date_to_string(forecast_time,h=True)+'.time.grb2'
            to_return['folder'] = self.forecast_dirs[protocal]['reforecast']+'/'+year+month +'/'
        else:
            to_return['filename'] = 'tmp2m.01.'+tools.date_to_string(forecast_time,h=True)+'.daily.grb2'
            to_return['folder'] = self.forecast_dirs[protocal]['operational']+'/'+year+'/'+year+month+'/'+year+month+day+'/'+year+month+day+hour+'/'
        
        to_return['full_path'] = protocal+'://' + self.host +'/' + to_return['folder'] + to_return['filename']
        return to_return[path_type]
    
    def reanalysis_url_from_timestamp(self, reanalysis_time, path_type='full_path', protocal='ftp'):
        assert path_type in ['full_path','folder','filename'] , 'unknown path type: '+str(path_type)
        assert protocal in ['http','ftp'] , 'unknown protocal: '+str(protocal)
        if isinstance(reanalysis_time, str):
            reanalysis_time = tools.string_to_date(reanalysis_time, h=False)
            
        year = reanalysis_time.strftime('%Y')
        month= reanalysis_time.strftime('%m')
        day  = reanalysis_time.strftime('%d')
        assert day=='01', 'CFS Reanalysis has 1 file for every month, so days other than 1 are not supported: ' + str(day)
        to_return={}
        if int(year) < 2011:
            to_return['filename'] = 'tmp2m.gdas.'+year+month+'.grb2'
            to_return['folder'] = self.reanalysis_dirs[protocal]['pre_2011']+'/'+year+month +'/'
        else:
            to_return['filename'] = 'tmp2m.gdas.'+year+month+'.grib2' #seriously NOAA? Can't even have consistent extensions?
            to_return['folder'] = self.reanalysis_dirs[protocal]['operational']+'/'+year+'/'+year+month+'/'
        
        to_return['full_path'] = protocal+'://' + self.host +'/' + to_return['folder'] + to_return['filename']
        return to_return[path_type]
    
    def last_n_forecasts(self, n = 10):
        all_forecasts = []
        latest_forecast_str = self.latest_forecast_time_str()
        latest_forecast_timestamp = tools.string_to_date(latest_forecast_str, h=True)
        
        all_forecasts.append({'initial_time':latest_forecast_str,
                              'download_url':self.forecast_url_from_timestamp(latest_forecast_timestamp, protocal='http')})
        
        six_hours = datetime.timedelta(hours=6)
        while len(all_forecasts) < n:
            latest_forecast_timestamp-=six_hours
            
            if not self.forecast_available(latest_forecast_timestamp):
                continue
            latest_forecast_str = tools.date_to_string(latest_forecast_timestamp, h=True)
            
            all_forecasts.append({'initial_time':latest_forecast_str,
                                  'download_url':self.forecast_url_from_timestamp(latest_forecast_timestamp, protocal='http')})
        return all_forecasts
    
    
# CFSv2 is has 6 hour timesteps, convert that to a daily mean
def cfs_to_daily_mean(cfs, cfs_initial_time):
    # times in the cfs forecasts are a delta from the initial time.
    # convert that to the actual date of the timestep.
    date_timestamps = np.datetime64(cfs_initial_time) + cfs.forecast_time.values
    cfs['forecast_time'] = date_timestamps
    
    # Aggregate to daily values instead of 6 hourly
    cfs = cfs.resample(forecast_time='1D').mean()
    
    return cfs

# Put the CFSv2 into a finer grained array
# This does not account for a different CRS, but actually changing the CRS results
# in minute differences. It also doesn't explicitely account for CFS being
# worldwide and prism being N. america. But the internals of xmap (a kdtree lookup)
# seem to deal with this fine.
def spatial_downscale(ds, target_array, data_var='tmean', time_dim='forecast_time'):
    assert isinstance(target_array, xr.DataArray), 'target array must be DataArray'
    ds_xmap = xmap.XMap(ds[data_var])
    ds_xmap.set_coords(x='lon',y='lat',t=time_dim)
    downscaled = ds_xmap.remap_like(target_array, xcoord='lon', ycoord='lat')
    return downscaled.to_dataset(name=data_var)

def open_cfs_grib(filename):
    return xr.open_dataset(filename, engine='pynio')

def process_forecast(forecast_filename, date, target_downscale_array=None,
                                  temp_folder=config['tmp_folder']):
   
    forecast_obj = open_cfs_grib(forecast_filename)
    
    # More reasonable variable names
    forecast_obj.rename({'lat_0':'lat', 'lon_0':'lon', 
                         'forecast_time0':'forecast_time',
                         'TMP_P0_L103_GGA0':'tmean'}, inplace=True)
    # Kelvin to celcius
    forecast_obj['tmean'] -= 273.15
    
    # 6 hourly timesteps to daily timesteps
    forecast_obj = cfs_to_daily_mean(cfs=forecast_obj, cfs_initial_time = date)
    
    # ~1.0 deg cfs grid to 4km prism grid.
    if target_downscale_array is not None:
        forecast_obj = spatial_downscale(ds = forecast_obj, 
                                              target_array = target_downscale_array)

    date64 = np.datetime64(date)
    # Make a new coordinate for the forecasts initial time so it can be 
    # differentiated from other forecasts
    forecast_obj = forecast_obj['tmean'].assign_coords(initial_time=date64).expand_dims(dim='initial_time').to_dataset()
    
    # New coordinate for the forecast lead time
    #lead_times = pd.TimedeltaIndex(forecast_obj.forecast_time - day64, freq='D')
    #forecast_obj = forecast_obj['tmean'].assign_coords(=date64).expand_dims(dim='initial_time').to_dataset()
    #initial_time_months = pd.DatetimeIndex(all_cfs.initial_time.values, freq='6H').to_period('M')

    return forecast_obj

def process_reanalysis(filename, date, target_downscale_array=None):
    obj = open_cfs_grib(filename)
    obj.load()
    
    # Keep only the primary 6 hour timesteps
    obj = obj.isel(forecast_time0=0).drop('forecast_time0')

    # More reasonable variable names
    obj.rename({'lat_0':'lat', 'lon_0':'lon', 
                'initial_time0_hours':'time',
                'TMP_P0_L103_GGA0':'tmean'}, inplace=True)
    
    # Kelvin to celcius
    obj['tmean'] -= 273.15
    
    # Don't need these
    obj = obj.drop(['initial_time0_encoded', 'initial_time0'])
    
    # Daily means
    obj = obj.resample(time='1D').mean()
    
    # ~1.0 deg cfs grid to 4km prism grid.
    if target_downscale_array is not None:
        assert isinstance(target_downscale_array, xr.DataArray), 'target array must be DataArray'
        obj = spatial_downscale(ds = obj, 
                                target_array = target_downscale_array,
                                time_dim='time')
    
    return obj