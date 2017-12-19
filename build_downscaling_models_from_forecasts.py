"""
Ideally I'd like to build downscaling models direclty from old forecasts, and this is
what that code did. But the data was just too big and this would have taken
forever, even with the hipergator. If I learn how do work with xarray better
I can come back ot this. 
"""

import xarray as xr
import pandas as pd
import numpy as np
from scipy.stats import linregress as lm
from tools import prism_tools, cfs_tools, tools
import os
import glob
import warnings


def collect_obs_data(historic_obs, month, ilat=None, ilon=None):
    obs_months = pd.DatetimeIndex(historic_obs.time.values).month

    data_values = historic_obs.isel(lat=ilat,lon=ilon, time=obs_months==month).tmean.values
    data_timestamps = historic_obs.isel(lat=ilat,lon=ilon, time=obs_months==month).time.values

    return {'data':data_values, 'timestamps':data_timestamps}

def collect_forecast_data(forecast_list, month, lead_time, ilat=1, ilon=1):
    data_values = np.array([])
    data_timestamps = np.array([]).astype(np.datetime64)
    # iterate over list of forecasts extracting all values 
    # in a particular month with a particular lead time
    for f in forecast_list:
        forecast_time_month = pd.DatetimeIndex(f.forecast_time.values).month
        initial_time_month = pd.Timestamp(f.initial_time.values[0]).month
        # Decide if this forecast file is worthy
        if month not in forecast_time_month:
            continue
        # need to account for 12 -> 1
        forecast_lead_times = np.array(forecast_time_month-initial_time_month)
        forecast_lead_times[forecast_lead_times<0] += 12
        days_with_correct_lead_time = forecast_lead_times==lead_time

        # Days in the forecast file in the appriate month and with appropriate lead time
        valid_days = np.logical_and(days_with_correct_lead_time, forecast_time_month==month)
        if np.any(valid_days):
            data_values = np.append(data_values, f.isel(forecast_time=valid_days, lon=ilon, lat=ilat).tmean.values)
            data_timestamps = np.append(data_timestamps, f.isel(forecast_time=valid_days, lon=ilon, lat=ilat).forecast_time.values)

    return {'data':data_values, 'timestamps':data_timestamps}


# Because of many forecasts every month, any given day
# will have multiple forecasted datapoints. The 
# observation data needs to be the same length. This will
# repeat each observed day the appropriate number of times
# to match the forecast data.
# f_data and o_data are dicts of {data, timestamps}, output
# from collect_xxx_data()
def reconcile_forecasts_and_obs(f_data, o_data):
    obs_dates_index=[]
    # TODO for loops are slow so I could mostly likely improve this
    for forecast_date in f_data['timestamps']:
        forecast_date_location_in_observations = np.where(forecast_date==o_data['timestamps'])[0]
        if len(forecast_date_location_in_observations)==0:
            warnings.warn('forecast date not available in obs')
            obs_dates_index.append(0)
        else:
            obs_dates_index.append(forecast_date_location_in_observations[0])
    o_data['data'] = o_data['data'][obs_dates_index]
    o_data['timestamps'] = o_data['timestamps'][obs_dates_index]
    return f_data, o_data

#############################################################
#############################################################
config = tools.load_config()

land_mask = xr.open_dataset(config['data_folder']+config['mask_file'])

historic_forecast_filenames = glob.glob(config['data_folder']+'cfsv2*')

historic_forecasts = [xr.open_dataset(f) for f in historic_forecast_filenames]
historic_observations = xr.open_dataset(config['historic_observations_file'])

lead_time_limit=6

# create a coefficient array to fill up with values
empty_array = np.ones((lead_time_limit, 12, land_mask.dims['lat'], land_mask.dims['lon']))
empty_array[:] = np.nan
model_coef=xr.Dataset({'slope':(('lead_time','month','lat','lon'), empty_array),
                       'intercept':(('lead_time','month','lat','lon'), empty_array)},
                      {'lat':land_mask.lat.values, 'lon':land_mask.lon.values,
                       'lead_time':np.arange(1,lead_time_limit+1), 'month':np.arange(1,13)})


total_pixels = land_mask.land.values.sum()
progress=0
pixel_processing_times=[]
import time
for lat_i in range(len(land_mask.lat)):
    for lon_i in range(len(land_mask.lon)):
        is_land = land_mask.isel(lat=lat_i,lon=lon_i).land.values
        if is_land:
            pixel_start_time=time.time()
            for month_i, month in enumerate(range(1,13)):
                for lead_time_i, lead_time in enumerate(range(1,lead_time_limit+1)):
                    forecasts = collect_forecast_data(historic_forecasts, month=month, lead_time=lead_time, ilat=lat_i, ilon=lon_i)
                    obs = collect_obs_data(historic_observations, month=month, ilat=lat_i, ilon=lon_i)
                    forecasts, obs = reconcile_forecasts_and_obs(forecasts, obs)

                    # The ranking step of the downscaling model
                    forecasts['data'].sort()
                    obs['data'].sort()

                    slope, intercept, *_ = lm(x=forecasts['data'], y=obs['data'])

                    model_coef['slope'][lead_time_i, month_i, lat_i, lon_i]=slope
                    model_coef['intercept'][lead_time_i, month_i, lat_i, lon_i]=intercept

            pixel_processing_times.append(round(time.time() - pixel_start_time, 1))
            print(str(progress)+'/'+str(total_pixels)+' pixels, '+str(pixel_processing_times[-1])+' sec')
            print('avg: '+str(np.mean(pixel_processing_times)))
