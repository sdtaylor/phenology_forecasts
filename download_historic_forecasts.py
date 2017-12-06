
import xarray as xr
import pandas as pd
import yaml
from tools import cfs_tools, tools
from mpi4py import MPI
import os
import time

with open('config.yaml', 'r') as f:
    config = yaml.load(f)

cfs = cfs_tools.cfs_ftp_info()


work_tag=0
stop_tag=1

def worker():
    comm = MPI.COMM_WORLD
    status = MPI.Status()
    
    worker_tmp_folder = config['tmp_folder']+str(MPI.COMM_WORLD.Get_rank()) + '/'
    os.makedirs(worker_tmp_folder, exist_ok=True)
    
    land_mask = xr.open_dataset(config['data_folder']+config['mask_file'])

    while True:        
        forecast_date = comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
        if status.Get_tag() == stop_tag: break
        start_time=time.time()
        forecast_obj = cfs_tools.download_and_process_forecast(cfs_info = cfs,
                                                               date=forecast_date,
                                                               temp_folder=worker_tmp_folder,
                                                               target_downscale_array=land_mask.to_array()[0])
    
        # Some issue with the processing
        if (not isinstance(forecast_obj, xr.Dataset)) and forecast_obj == -1:
            print('Processing error for date: '+str(forecast_date))
            return_data={'status':1,'forecast_date':forecast_date}
        else:
            processed_filename = config['data_folder']+'cfsv2_'+tools.date_to_string(forecast_date,h=True)+'.nc'
            time_dims = len(forecast_obj.forecast_time)
            forecast_obj.to_netcdf(processed_filename, encoding={'tmean': {'zlib':True, 'complevel':1, 'chunksizes':(1,time_dims,10,10)}})
            tools.cleanup_tmp_folder(worker_tmp_folder)
            return_data={'status':0,'forecast_date':forecast_date}
        
        return_data['processing_time_min'] = round(time.time() - start_time,0)/60
        comm.send(obj=return_data, dest=0)
    
def boss():
    comm = MPI.COMM_WORLD
    status = MPI.Status()
    num_workers = MPI.COMM_WORLD.Get_size()

    ##############################################
    # Collect information on available CFS forecasts
    # TODO: extend this for the full years
    begin_date = tools.string_to_date(str(config['historic_years_begin'])+'0101', h=False)
    end_date = tools.string_to_date(str(config['historic_years_end'])+'1231', h=False)
    
    # CFS has forecasts every 6 hours
    date_range_6h = pd.date_range(begin_date, end_date, freq='6H').to_pydatetime()
    
    cfs = cfs_tools.cfs_ftp_info()
    
    # Check which ones are available. After 2011 they are available every day,
    # every 6 hours. But reforecasts from 1982-2010 are only every 5th day
    date_range_6h = [d for d in date_range_6h if cfs.forecast_available(d)]
    
    num_jobs = len(date_range_6h)
    
    #Dole out the first round of jobs to all workers
    for i in range(1, num_workers):
        d = date_range_6h.pop()
        comm.send(obj = d, dest=i, tag=work_tag)
    
    #While there are new jobs to assign.
    #Collect results and assign new jobs as others are finished.
    results = []
    while len(date_range_6h)>0:
        next_job_date = date_range_6h.pop()
        job_result = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
        results.append(job_result)
        num_finished_jobs=len(results)
        print('completed: ' +str(num_finished_jobs)+'/'+str(num_jobs) +' , ' + \
              str(job_result['forecast_date']) + ' ' + str(job_result) + ' ' + \
              str(job_result['processing_time_min']))
    
        comm.send(obj=next_job_date, dest=status.Get_source(), tag=work_tag)

    #Collect last jobs
    for i in range(1, num_workers):
        job_result = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG)
        results.append(job_result)
        
    #Shut down all workers
    for i in range(1, num_workers):
        comm.send(obj=None, dest=i, tag=stop_tag)
        
        
if __name__ == "__main__":
    rank = MPI.COMM_WORLD.Get_rank()
    name = MPI.Get_processor_name()
    size = MPI.COMM_WORLD.Get_size()

    if rank == 0:
        print('boss '+str(rank)+' on '+str(name))
        boss()
    else:
        print('worker '+str(rank)+' on '+str(name))
        worker()