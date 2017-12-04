
import xarray as xr
import pandas as pd
import numpy as np
import yaml
from tools import prism_tools, cfs_tools, tools
import os
import glob


def collect_obs_data(historic_obs, month, lat=1, lon=1):
    obs_months = pd.DatetimeIndex(historic_obs.time.values).month

    data_values = historic_obs.isel(lat=lat,lon=lon, time=obs_months==month).tmean.values
    data_timestamps = historic_obs.isel(lat=lat,lon=lon, time=obs_months==month).time.values

    return data_values, data_timestamps

def collect_forecast_data(forecast_list, month, lead_time, lat=1, lon=1):
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
            data_values = np.append(data_values, f.isel(forecast_time=valid_days, lon=lon, lat=lat).tmean.values)
            data_timestamps = np.append(data_timestamps, f.isel(forecast_time=valid_days, lon=lon, lat=lat).forecast_time.values)

    return data_values, data_timestamps


def reconcile_forecasts_and_obs(f_data, o_data):
    pass

with open('config.yaml', 'r') as f:
    config = yaml.load(f)

historic_forecast_filenames = glob.glob(config['data_folder']+'cfsv2*')

historic_forecasts = [xr.open_dataset(f) for f in historic_forecast_filenames]
historic_observations = xr.open_dataset(config['historic_observations_file'])

july_forecasts = collect_forecast_data(historic_forecasts, month=7, lead_time=1, lat=300, lon=700)
july_obs = collect_obs_data(historic_observations, month=7, lat=300, lon=700)

#for month in range(1,13):
#    for lead_time in range(1:7):
        # get forecast data

