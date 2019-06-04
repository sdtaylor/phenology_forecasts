#######

target_season=2018
doy_0 = '2018-01-01'

observation_site_info_file = 'evaluation/phenology_data_2018/ancillary_site_data.csv'
observation_file = 'evaluation/phenology_2018_observations.csv'

final_hindcast_file = 'evaluation/hindcast_data_2018.csv'

n_prediction_jobs=32
######
# Climate stuff
num_climate_ensemble = 5
climate_lead_time = 36 # This is in weeks

##
#num_hipergator_workers=400
num_hipergator_workers=120

dask_port=8786
dask_scheduler_address='127.0.0.1:8786'
dask_scheduler_file = '/home/shawntaylor/dask_scheduler.json'

num_head_workers=2
##
#  Run a hindcast every 4 days
# Start, end, and stepsize of when to run hindcasts
#begin_date = '20180402'
#end_date   = '20180601'
begin_date = '20171102'
end_date   = '20180330'
frequency = '4D'


