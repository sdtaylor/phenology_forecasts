from ftplib import FTP
import datetime
import xarray as xr
import numpy as np
import os
import zipfile
import time
import urllib
from tools import tools

config = tools.load_config()

# Ways to query the PRISM ftp server in meaningful and efficient ways
class prism_ftp_info:
    def __init__(self, host='prism.nacse.org', 
                 base_dir='daily/tmean', 
                 user='anonymous',passwd='abc123'):
        self.host=host
        self.user=user
        self.passwd=passwd
        
        self.base_dir=base_dir
        self._folder_file_lists={}
        
        self.connect()
    
    def _query_ftp_folder(self, folder, attempt=1):
        connect_attempts=3
        retry_wait_time=300
        try:
            dir_listing = self.con.nlst(folder)
            return dir_listing
        except:
            if attempt + 1 == connect_attempts:
                raise IOError('Cannot query PRISM ftp')
            else:
                print('Cannot query PRISM folder, reconnecting and retrying in {t} sec'.format(t=retry_wait_time))
                time.sleep(retry_wait_time)
                self.close()
                self.connect()
                return self._query_ftp_folder(folder, attempt=attempt+1)
    
    def connect(self):
        self.con = FTP(host=self.host, user=self.user, passwd=self.passwd)

    def close(self):
        self.con.close()
        
    #Ensure that each folder is only queried once
    def _get_folder_listing(self, folder):
        if folder in self._folder_file_lists:
            return self._folder_file_lists[folder]
        else:
            dir_listing = self._query_ftp_folder(folder)
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
    
    def date_available(self, date):
        return self.get_date_status(date)!=None
        
# a single xarray day matching dataset d
# with NA values and status = None
def make_blank_day_like(d):
    pass

def current_growing_season():
    today = datetime.datetime.today()
    year = today.strftime('%Y')
    season_begin = year+config['season_month_begin']+config['season_day_begin']
    cutoff = datetime.datetime.strptime(season_begin, '%Y%m%d')
    if today >  cutoff:
        year = str(int(year) + 1)
    return year

def round_to_current_day(t):
    return t - datetime.timedelta(hours=t.hour, 
                                  minutes=t.minute, 
                                  seconds=t.second, 
                                  microseconds=t.microsecond)

def prism_to_xarray(bil_filename, varname, date, status, mask_value=-9999):
    bil = xr.open_rasterio(bil_filename)
    lon, lat = bil.x.values, bil.y.values
    data=bil.values
    data[data==mask_value]=np.nan
    date = np.datetime64(date)
    
    xr_dataset = xr.Dataset(data_vars = {varname: (('time','lat','lon'), data),
                                         'status':(('time'), [status])},
                            coords =    {'time':[date],'lat':lat, 'lon':lon},
                            attrs =     {'crs':bil.crs,
                                         'units':'C'})

    return xr_dataset

# Download a file for a particualar day and convert to an
# xarray object for inclusion in main dataset
def download_and_process_day(download_url, date, varname, status):
    dest_path  = config['tmp_folder']+os.path.basename(download_url)
    tools.download_file(download_path=download_url,
                        dest_path=dest_path)
    z = zipfile.ZipFile(dest_path, 'r')
    z.extractall(path = config['tmp_folder'])
    z.close()
    bil_filename = dest_path.split('.')[0]+'.bil'
    return prism_to_xarray(bil_filename, varname=varname, date=date, status=status)

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

def update_day(ds, new_day_ds):
    to_keep = ds.time.values!=new_day_ds.time.values
    ds = ds.isel(time=to_keep).copy()
    return ds.merge(new_day_ds)