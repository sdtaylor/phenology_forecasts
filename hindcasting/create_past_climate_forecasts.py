import pandas as pd
import numpy as np
import glob
import datetime
from time import sleep
from tools import tools
#from tools.phenology_tools import predict_phenology_from_climate
from automated_forecasting.climate import cfs_forecasts
#from automated_forecasting.phenology import apply_phenology_models
from pyPhenology import utils

config = tools.load_config()


######
# Climate stuff
num_climate_ensemble = 5
climate_lead_time = 36 # This is in weeks
num_hipergator_workers=10

hindcast_begin_date = tools.string_to_date('20180101', h=False)
hindcast_end_date   = tools.string_to_date('20180401', h=False)
#  Run a hindcast every 4 days
date_range=pd.date_range(hindcast_begin_date, hindcast_end_date, freq='4D').to_pydatetime()

current_season_observed_file = config['current_season_observations_file']

######
# Other stuff

current_season=2018

doy_0 = np.datetime64('2018-01-01')

today = datetime.datetime.today().date()

import xarray as xr


# For spatial reference
land_mask = xr.open_dataset(config['mask_file'])

#####################################################
# I am having issues on the hipergator where these locations
# are missing some, but not all, temperature values. I can't 
# figure out, or reproduce it on serenity. 11 pixels is nothing
# so I'm just going to mark them all NA and move on. 
def hipergator_correction(climate_forecast):
    bad_pixels_axis_1 = np.array([ 47,  51,  68, 128, 139, 143, 213, 238, 372, 411, 440])
    bad_pixels_axis_2 = np.array([ 700,  794,  506, 1220,  595,  626, 1179,  688,  516,  481,  463])
    
    climate_forecast['tmean'][:,bad_pixels_axis_1,bad_pixels_axis_2] = np.nan

######################################################
for date_i, hindcast_issue_date in enumerate(date_range):
    
    ##################################
    # process the climate forecasts for this date
    climate_forecast_folder = config['data_folder']+'past_climate_forecasts/'+str(hindcast_issue_date.date())+'/'
    tools.make_folder(climate_forecast_folder)
    # Make the observed climate only up to the prior day of the forecast date
    current_season_observed = xr.open_dataset(current_season_observed_file)
    observed_days_to_keep = current_season_observed.time < np.datetime64(hindcast_issue_date)
    current_season_observed = current_season_observed.sel(time=observed_days_to_keep)
    
    # Download and process climate forecasts
    cfs_forecasts.get_forecasts_from_date(forecast_date=hindcast_issue_date,
                                          destination_folder=climate_forecast_folder,
                                          lead_time = climate_lead_time,
                                          forecast_ensemble_size=num_climate_ensemble,
                                          current_season_observed=current_season_observed)
