from tools import tools
import time
import datetime
import subprocess
import pandas as pd
import yaml

from automated_forecasting.climate import download_latest_observations, cfs_forecasts
from automated_forecasting.phenology import apply_phenology_models

#########################################################
# From this script the following is run:
#    - download the latest prism temperature observations
#    - download and processes the latest CFSv2 forecasts
#    - apply all the phenology models  

#This is designed to run on a remote, potentially temporary, server
#separate from the one that hosts the cron job. Though this script
#does not move the generated data (ie. phenology_forecast_YYYY_MM_DD.nc)
#to another server, it potentially could at the end. 
#Currently run_automated_forecast.py does the data moving.

#########################################################
#####################
divider='#'*90 + '\n'
big_divider = divider*3
def message(m):
    print(big_divider)
    print(m)
    print(big_divider)
#####################
start_time = time.time()
def min_elapsed(start_time=start_time):
    return str(round((time.time() - start_time)/60, 2))
#####################
    
config = tools.load_config()
now = datetime.datetime.now
today = str(now().date())

run_info = {'date':today}

# write the run_info.json file with a failure reason
def write_failed_run_info(failure_reason):
    run_info['status'] = 'failed'
    run_info['failure_reason'] = failure_reason
    tools.write_json(run_info, config['run_status'])


message('Starting automated forecasting ' + str(now()))

# Clear the climate forecast folder
tools.cleanup_tmp_folder(config['current_forecast_folder'])
###############################
# Update prism observations
message('Downloading latest observations ' + str(now()))
try:
    download_latest_observations.run()
    message(min_elapsed() + ' min in downloading latest observations succeeded ' + str(now()))
except:
    message(min_elapsed() + ' min in downloading latest observations failed ' + str(now()))
    write_failed_run_info('failed downloading/processing prism data')
    raise
###############################
# Get the latest climate forecasts
message('Downloading latest forecasts ' + str(now()))
try:
    cfs_forecasts.get_forecasts_from_date(forecast_date = now(),
                                          destination_folder = config['current_forecast_folder'])
    message(min_elapsed() + ' min in downloading latest forecasts succeeded ' + str(now()))
except:
    message(min_elapsed() + ' min in downloading latest forecasts failed ' + str(now()))
    write_failed_run_info('failed downloading/processing climate forecasts')
    raise

###############################
# apply phenology models
message('Applying phenology models ' + str(now()))
try:
    phenology_forecast_path = apply_phenology_models.run()
    message(min_elapsed() + ' min in phenology models succeeded ' + str(now()))
except:
    message(min_elapsed() + ' min in phenology models failed ' + str(now()))
    write_failed_run_info('failed applying phenology models')
    raise

# write the run_info.json file with a success status and relavant info
run_info['status'] = 'success'
run_info['phenology_forecast_path'] = phenology_forecast_path
tools.write_json(run_info, config['run_status'])

message('Automated forecasting finished at ' + str(now()))

tools.cleanup_tmp_folder(config['tmp_folder'])
