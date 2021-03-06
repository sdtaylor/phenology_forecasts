import xarray as xr
from ftplib import FTP
import ftplib
import datetime
import numpy as np
import xmap
import os
from warnings import warn
import urllib
import time
from tools import tools

config = tools.load_config()

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

        # Do not connect t the ftp by default
        #self.connect()
        self._folder_file_lists={}
    
    def connect(self, attempts_made=0):
        warn('noaa FTP server has been down for a while')
        connect_attempts=5
        retry_wait_time=300
        try:
            self.con = FTP(host=self.host, user='anonymous', passwd='abc123')
        except:
            if attempts_made + 1 == connect_attempts:
                raise IOError('Cannot connect to CFS ftp after {n} attempts'.format(n=connect_attempts))
            else:
                print('Cannot connect to CFS ftp, retrying in {t} sec'.format(t=retry_wait_time))
                time.sleep(retry_wait_time)
                self.connect(attempts_made = attempts_made + 1)
    
    def close(self):
        if hasattr(self, 'con'):
            self.con.close()
        else:
            pass
    
    def _query_ftp_folder(self, folder, attempts_made=0):
        connect_attempts=5
        # wait longer and longer between retries before failing entirely.
        retry_wait_times=[60,600,3600,3600*2,3600*4]
        try:
            dir_listing = self.con.nlst(folder)
            return dir_listing
        # This is a 450 error, aka folder not found, so return as empty
        except ftplib.error_temp:
            return []
        # Other errors are likely connection issues
        except:
            if attempts_made + 1 == connect_attempts:
                raise IOError('Cannot query CFS ftp after {n} attempts'.format(n=connect_attempts))
            else:
                print('Cannot query CFS folder, reconnecting and retrying in {t} sec'.format(t=retry_wait_times[attempts_made]))
                time.sleep(retry_wait_times[attempts_made])
                self.close()
                time.sleep(1)
                self.connect()
                return self._query_ftp_folder(folder, attempts_made = attempts_made + 1)
    
    #Ensure that each folder is only queried once
    def _get_folder_listing(self, folder):
        if folder in self._folder_file_lists:
            return self._folder_file_lists[folder]
        else:
            dir_listing = self._query_ftp_folder(folder)
            self._folder_file_lists[folder]=dir_listing
            return dir_listing
        
    def forecast_available(self, forecast_time):
        if isinstance(forecast_time, str):
            forecast_time = tools.string_to_date(forecast_time, h=True)
        
        # 2011 to present is pretty complete, and also time consuming
        # to check. So of it's in this range just assume it's there
        cutoff_begin = tools.string_to_date('2011040100', h=True)
        cutoff_end   = tools.string_to_date('2017070100', h=True)
        if forecast_time >= cutoff_begin and forecast_time <= cutoff_end:
            return True
        
        forecast_filename = self.forecast_url_from_timestamp(forecast_time, path_type='full_path',
                                                             protocal='http')
        return tools.file_available(forecast_filename)
    
    # TODO: variable filename to download precip as well
    # forecast download paths look like: 
    # ftp://nomads.ncdc.noaa.gov/modeldata/cfsv2_forecast_ts_9mon/2017/201711/20171111/2017111118/tmp2m.01.2017111118.daily.grb2
    # reforecast paths (prior to 2011) are:
    # ftp://nomads.ncdc.noaa.gov/CFSRR/cfsr-rfl-ts9/tmp2m/200808/tmp2m.2008080418.time.grb2
    # path_types: 
    # folder returns the containing folder but not the protocal or 
    # filename returns only the filename
    # full path returns the full download link
    def forecast_url_from_timestamp(self, forecast_time, path_type='full_path', protocal='http'):
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
    
    def reanalysis_url_from_timestamp(self, reanalysis_time, path_type='full_path', protocal='http'):
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
    
    def last_n_forecasts(self, from_date=None, n = 10):
        # The first timestamp to check for is the 18:00 interation of the day
        # prior to the specified date, or if no date is specific, from the current date.
        # 
        
        if not from_date:
            from_date = tools.date_to_string(datetime.datetime.today()) + '00'
        else:
            from_date = tools.date_to_string(from_date) + '00'
        
        # This is hour 00 of the specified date. it will become hour 1800
        # in the first iteration of the while loop
        latest_forecast_timestamp = tools.string_to_date(from_date, h=True)
        
        six_hours = datetime.timedelta(hours=6)
        
        all_forecasts = []
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
def spatial_downscale(ds, target_array, method, data_var='tmean', 
                      time_dim='forecast_time', downscale_args={}):
    assert isinstance(target_array, xr.DataArray), 'target array must be DataArray'
    ds_xmap = xmap.XMap(ds[data_var], debug=False)
    ds_xmap.set_coords(x='lon',y='lat',t=time_dim)
    downscaled = ds_xmap.remap_like(target_array, xcoord='lon', ycoord='lat',
                                    how=method, **downscale_args)
    return downscaled.to_dataset(name=data_var)

def open_cfs_grib(filename):
    return xr.open_dataset(filename, engine='pynio')

def convert_cfs_grib_forecast(local_filename, date, target_downscale_array=None,
                              add_initial_time_dim=True,
                              downscale_method='nearest',
                              temp_folder=config['tmp_folder']):
   
    forecast_obj = open_cfs_grib(local_filename)
    
    # More reasonable variable names
    forecast_obj.rename({'lat_0':'lat', 'lon_0':'lon', 
                         'forecast_time0':'forecast_time',
                         'TMP_P0_L103_GGA0':'tmean'}, inplace=True)
    # Kelvin to celcius
    forecast_obj['tmean'] -= 273.15
    
    # 6 hourly timesteps to daily timesteps
    forecast_obj = cfs_to_daily_mean(cfs=forecast_obj, cfs_initial_time = date)

    if add_initial_time_dim:
        date64 = np.datetime64(date)
        # Make a new coordinate for the forecasts initial time so it can be 
        # differentiated from other forecasts
        forecast_obj = forecast_obj['tmean'].assign_coords(initial_time=date64).expand_dims(dim='initial_time').to_dataset()
        
        # New coordinate for the forecast lead time
        #lead_times = pd.TimedeltaIndex(forecast_obj.forecast_time - day64, freq='D')
        #forecast_obj = forecast_obj['tmean'].assign_coords(=date64).expand_dims(dim='initial_time').to_dataset()
        #initial_time_months = pd.DatetimeIndex(all_cfs.initial_time.values, freq='6H').to_period('M')

    return forecast_obj

def process_reanalysis(filename, date, 
                       downscale_method='nearest',
                       target_downscale_array=None):
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
                                method=downscale_method,
                                downscale_args={'k':2},
                                target_array = target_downscale_array,
                                time_dim='time')
    
    return obj
