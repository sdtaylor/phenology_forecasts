from tools import tools
import time
import os
import datetime
import subprocess
import pandas as pd

#########################################################
# This is the primary script run by the cron job. From
# here the remote hipergator job is kicked off, with the 
# resulting phenology_forecast_YYYY_MM_DD.nc netCDF file
# obtained afterwards. Then the static images are generated
# and finally things synced to the server. 

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

###############################
# Start the hipergator job and wait for it to finish
remote_control = tools.RemoteRunControl(con_info = config['remote_connection_info'],
                                        remote_status_filename=config['run_status'])

remote_control.clear_status_file()

remote_control.submit_job(remote_job_script=config['slurm_job_script'])
message('job submitted at ' + str(now()))

while not remote_control.remote_run_complete():
    time.sleep(60*10)

run_info = remote_control.remote_run_info()

if run_info['status'] == 'failed':
    message('remote run failed. reason: ' + run_info['failure_reason'])
    quit()
else:
    message('remote run succeeded at ' + str(now()))

###############################
# Get the resulting file
local_phenology_forecast_path = config['phenology_forecast_folder'] + os.path.basename(run_info['phenology_forecast_path'])

transfer_successful = remote_control.get_file(remote_path=run_info['phenology_forecast_path'],
                                              local_path=local_phenology_forecast_path)

if not transfer_successful:
    message('transfering phenology foreast file failed')
    quit()
    
###############################
# Rebuild the website
message('Updating phenology forecast website ' + str(now()))
# Generate all the static forecast images
try:
    subprocess.call(['/usr/bin/Rscript',
                     '--vanilla',
                     'automated_forecasting/presentation/build_png_maps.R',
                     local_phenology_forecast_path])
    message('building static images succeeded ' + str(now()))
except:
    message('building static images failed ' + str(now()))
    raise

# Sync the images folder and update site metadata.
from automated_forecasting.presentation import sync_website
message('Syncing website data' + str(now()))
try:
    sync_website.run(update_all_images=True)
    message('Syncing website data succeeded')
except:
    message('Syncing website data failed')
    raise

message('Automated forecasting finished at ' + str(now()))

tools.cleanup_tmp_folder(config['tmp_folder'])
