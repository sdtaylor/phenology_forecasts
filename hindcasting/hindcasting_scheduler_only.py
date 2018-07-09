from time import sleep
from tools import tools

import hindcast_config
config = tools.load_config()

######################################################
# Setup dask cluster
######################################################
from dask_jobqueue import SLURMCluster
from dask.distributed import Client
from dask import delayed
cluster = SLURMCluster(processes=1,queue='hpg2-compute', threads=2, memory='10GB', walltime='144:00:00',
                       death_timeout=600, local_directory='/tmp/', scheduler_port=hindcast_config.dask_port)
# Write out the scheduler file manually
# taken from distributed.scheduler.py
import json
with open(hindcast_config.dask_scheduler_file, 'w') as f:
    json.dump(cluster.scheduler.identity(), f, indent=2)

print('Starting up workers')
workers = cluster.start_workers(hindcast_config.num_hipergator_workers)
dask_client = Client(scheduler_file=hindcast_config.dask_scheduler_file)

wait_time=0
while len(dask_client.scheduler_info()['workers']) < hindcast_config.num_hipergator_workers:
    print('waiting on workers: {s} sec. so far'.format(s=wait_time))
    sleep(10)
    wait_time+=10
    
    # If 5 minutes goes by try adding them again
    if wait_time > 300:
        workers.extend(cluster.start_workers(1))

print('All workers accounted for')


# Wait patiently until it gets killed
while True:
    sleep(60)
