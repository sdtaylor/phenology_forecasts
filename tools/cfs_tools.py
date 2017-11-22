import xarray as xr
from ftplib import FTP
import datetime
import numpy as np
import xmap


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
        
    def latest_forecast_time_str(self, dirs_in_tree=4):
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
    
    # TODO: variable filename to download precip as well
    # Download paths look like: 
    #ftp://nomads.ncdc.noaa.gov/modeldata/cfsv2_forecast_ts_9mon/2017/201711/20171111/2017111118/tmp2m.01.2017111118.daily.grb2
    def _build_full_path(self, forecast_time):
        year = forecast_time.strftime('%Y')
        month= forecast_time.strftime('%m')
        day  = forecast_time.strftime('%d')
        hour = forecast_time.strftime('%H')
        
        filename = 'tmp2m.01.'+self._date_to_string(forecast_time)+'.daily.grb2'
        full_path = 'http://'+self.host+'/'+self.base_dir+'/'
        full_path+= year+'/'+year+month+'/'+year+month+day+'/'+year+month+day+hour+'/'
        full_path+= filename
        return full_path
        
    def last_n_forecasts(self, n = 10):
        all_forecasts = []
        latest_forecast_str = self.latest_forecast_time_str()
        latest_forecast_timestamp = self._string_to_date(latest_forecast_str)
        
        all_forecasts.append({'initial_time':latest_forecast_str,
                              'download_url':self._build_full_path(latest_forecast_timestamp)})
        
        six_hours = datetime.timedelta(hours=6)
        for i in range(n-1):
            latest_forecast_timestamp-=six_hours
            latest_forecast_str = self._date_to_string(latest_forecast_timestamp)
            
            all_forecasts.append({'initial_time':latest_forecast_str,
                                  'download_url':self._build_full_path(latest_forecast_timestamp)})
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
def spatial_downscale(ds, target_array):
    ds_xmap = xmap.XMap(ds['tmean'])
    ds_xmap.set_coords(x='lon',y='lat',t='forecast_time')
    downscaled = ds_xmap.remap_like(target_array, xcoord='lon', ycoord='lat')
    return downscaled.to_dataset(name='tmean')

def open_cfs_forecast(filename):
    return xr.open_dataset(filename, engine='pynio')