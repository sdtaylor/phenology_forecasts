#import xarray as xr
import datetime
import xarray as xr
import numpy as np
import pandas as pd
import os
from tools import prism_tools, tools

config = tools.load_config()

def build_climate_observations(season, first_date=None, end_date=None, filename=None):
    """"
    Build an xarray object of all the daily observed prims values in a season
    
    filename: 
        filename to save as. If None it will return the xarray object
    """
    prism = prism_tools.prism_ftp_info()
    today = datetime.datetime.today().date()
    if not first_date:
        first_date = str(int(season)-1) + config['season_month_begin'] + config['season_day_begin']
        first_date = tools.string_to_date(first_date, h=False).date()
        assert first_date < today, 'Beginning of season hasnt happened yet'
        
    if not end_date:
        end_date = today
        
    prism_days_to_add = pd.date_range(np.datetime64(first_date), np.datetime64(end_date), closed='right')
    
    for i, day in enumerate(prism_days_to_add):
        day = day.to_pydatetime()
        day_status = prism.get_date_status(day)
        if day_status is not None:
            print('adding prism day ' + str(day))
            day_url = prism.get_download_url(day)
            day_xr= prism_tools.download_and_process_day(download_url=day_url,
                                                         date=day,
                                                         varname='tmean',
                                                         status=day_status)
            if i==0:
                observed_weather = day_xr
            else:
                observed_weather = observed_weather.merge(day_xr)
        else:
            pass
    
    if filename:
        observed_weather.to_netcdf(filename)
    else:
        return observed_weather