from tools import tools
import time
import datetime

from automated_forecasting.climate import download_latest_observations, download_latest_forecasts
from automated_forecasting.phenology import apply_phenology_models

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
    raise
###############################
# Get the latest climate forecasts
message('Downloading latest forecasts ' + str(now()))
try:
    download_latest_forecasts.run()
    message(min_elapsed() + ' min in downloading latest forecasts succeeded ' + str(now()))
except:
    message(min_elapsed() + ' min in downloading latest forecasts failed ' + str(now()))
    raise

###############################
# apply phenology models
message('Applying phenology models ' + str(now()))
try:
    apply_phenology_models.run()
    message(min_elapsed() + ' min in phenology models succeeded ' + str(now()))
except:
    message(min_elapsed() + ' min in phenology models failed ' + str(now()))
    raise

###############################
# rebuild website
# TODO

tools.cleanup_tmp_folder(config['tmp_folder'])