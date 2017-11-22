#import xarray as xr
import datetime
import xarray as xr
import numpy as np
import pandas as pd
import yaml
import os
from tools import prism_utils

with open('config.yaml', 'r') as f:
    config = yaml.load(f)

if __name__=='__main__':
    data_dir = config['data_folder']
    current_season=prism_utils.current_growing_season()
    observed_weather_file = data_dir+current_season+'_observed_weather.nc'
    
    if os.path.isfile(observed_weather_file):
        observed_weather = xr.open_dataset(observed_weather_file)
    else:
        print('observed weather file not found')
    
    today = prism_utils.round_to_current_day(datetime.datetime.today())
    yesterday = today - datetime.timedelta(days=1)
    
    # The last entry in this seasons observed weather
    latest_observed_day = observed_weather.time.values[-1]
    
    prism_days_to_add = pd.date_range(latest_observed_day, np.datetime64(yesterday), closed='right')
    
    prism = prism_utils.prism_ftp_info()
    
    # TODO: download all of them
    for day in prism_days_to_add[0:3]:
        day = day.to_pydatetime()
        day_status = prism.get_date_status(day)
        if day_status is not None:
            day_xr= prism_utils.download_and_process_day(prism_info=prism, date=day,
                                                         varname='tmean', status=day_status)
            observed_weather = observed_weather.combine_first(day_xr)
        else:
            pass
            # make a blank array for this day with status None
        
    # Iterate thru the weather xarray again and attempt to update
    # anything that has changed status
    for day in observed_weather.time.values:
        current_status = observed_weather.sel(time=day).status.values.tolist()
        ftp_status = prism.get_date_status(pd.Timestamp(day).to_pydatetime())
        if prism_utils.newer_file_available(current_status, ftp_status):
            day = pd.Timestamp(day).to_pydatetime()
            updated_day_xr = prism_utils.download_and_process_day(prism_info=prism, date=day,
                                                                  varname='tmean', status=ftp_status)
            observed_weather = prism_utils.update_day(observed_weather, updated_day_xr)
            
            print('file_to_update')

    
    prism.close()
    prism_utils.cleanup_tmp_folder()












