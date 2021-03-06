#import xarray as xr
import datetime
import xarray as xr
import numpy as np
import pandas as pd
import os
from tools import prism_tools, tools

config = tools.load_config()

def run():
    current_season=tools.current_growing_season(config)
    observed_weather_file = config['current_season_observations_file']
    
    today = datetime.datetime.today().date()
    yesterday = today - datetime.timedelta(days=1)
    
    print('Downloading latest PRISM observations for season ' + str(current_season))
    print('Todays date: ' + str(today))
    
    prism = prism_tools.prism_ftp_info()

    
    if os.path.isfile(observed_weather_file):
        observed_weather = xr.open_dataset(observed_weather_file)
        # The last entry in this seasons observed weather
    else:
        # Initiate this seasons observed weather
        first_day = str(int(current_season)-1) + config['season_month_begin'] + config['season_day_begin']
        first_day = tools.string_to_date(first_day, h=False).date()
        assert first_day < today, 'Beginning of season hasnt happened yet'
        first_day_status = prism.get_date_status(first_day)
        assert first_day_status is not None, 'Data from first day of season not available: ' + str(first_day)
        first_day_url = prism.get_download_url(first_day)
        observed_weather = prism_tools.download_and_process_day(download_url=first_day_url,
                                                                date=first_day,
                                                                varname='tmean',
                                                                status=first_day_status)
        observed_weather.to_netcdf(config['current_season_observations_file'])
    
    latest_observed_day = observed_weather.time.values[-1]
    print('most recent observed date on file: ' + str(latest_observed_day))
    prism_days_to_add = pd.date_range(latest_observed_day, np.datetime64(yesterday), closed='right')
    
    # Force the daily status to unicode. Otherwise xarray gets very confused
    observed_weather['status'] = observed_weather.status.astype('<U11')
    
    # TODO: download all of them
    for day in prism_days_to_add:
        day = day.to_pydatetime()
        day_status = prism.get_date_status(day)
        print(day_status)
        if day_status is not None:
            print('adding prism day ' + str(day))
            day_url = prism.get_download_url(day)
            day_xr= prism_tools.download_and_process_day(download_url=day_url,
                                                         date=day,
                                                         varname='tmean',
                                                         status=day_status)
            observed_weather = observed_weather.merge(day_xr)
        else:
            pass
            # make a blank array for this day with status None
    
    if len(prism_days_to_add)==0:
        print('No days to add')
    
    # Iterate thru the weather xarray again and attempt to update
    # anything that has changed status
    days_updated=0
    for day in observed_weather.time.values:
        current_status = observed_weather.sel(time=day).status.values.tolist()
        ftp_status = prism.get_date_status(pd.Timestamp(day).to_pydatetime())
        if prism_tools.newer_file_available(current_status, ftp_status):
            day = pd.Timestamp(day).to_pydatetime()
            print('updating day {d} from {s1} to {s2}'.format(d=day, s1=current_status, s2=ftp_status))
            day_url = prism.get_download_url(day)
            updated_day_xr = prism_tools.download_and_process_day(download_url=day_url,
                                                                  date=day,
                                                                  varname='tmean',
                                                                  status=ftp_status)
            observed_weather = prism_tools.update_day(observed_weather, updated_day_xr)
            days_updated+=1
    
    if days_updated==0:
        print('No days updated to newer version')

    observed_weather.load()
    observed_weather.close()
    os.remove(config['current_season_observations_file'])
    observed_weather.to_netcdf(config['current_season_observations_file'])
    
    prism.close()
    tools.cleanup_tmp_folder(config['tmp_folder'])


if __name__=='__main__':
    run()
