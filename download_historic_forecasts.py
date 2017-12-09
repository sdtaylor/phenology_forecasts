
import xarray as xr
import pandas as pd
import yaml
from tools import cfs_tools, tools
from mpi4py import MPI
import os
import time

with open('config.yaml', 'r') as f:
    config = yaml.load(f)

work_tag=0
stop_tag=1

def worker():
    comm = MPI.COMM_WORLD
    status = MPI.Status()
    
    worker_tmp_folder = config['tmp_folder']+str(MPI.COMM_WORLD.Get_rank()) + '/'
    os.makedirs(worker_tmp_folder, exist_ok=True)
    
    land_mask = xr.open_dataset(config['data_folder']+config['mask_file'])

    while True:        
        forecast_details = comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
        if status.Get_tag() == stop_tag: break
        download_url = forecast_details['download_url']
        forecast_date = forecast_details['forecast_date']
        forecast_filename = worker_tmp_folder + os.path.basename(download_url)
        start_time=time.time()
        
        download_status = tools.download_file(download_path=download_url, dest_path=forecast_filename)

    
        # Some issue with the downloading
        if download_status != 0:
            print('Download error for date: '+str(forecast_date))
            return_data={'status':1,'forecast_date':forecast_date}
        else:
            forecast_obj = cfs_tools.process_forecast(forecast_filename=forecast_filename,
                                                      date=forecast_date,
                                                      temp_folder=worker_tmp_folder,
                                                      target_downscale_array=land_mask.to_array()[0])
            processed_filename = config['data_folder']+'cfsv2_'+tools.date_to_string(forecast_date,h=True)+'.nc'
            time_dims = len(forecast_obj.forecast_time)
            forecast_obj.to_netcdf(processed_filename, encoding={'tmean': {'zlib':True, 
                                                                           'complevel':1, 
                                                                           'chunksizes':(1,time_dims,10,10)}})
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
    
    # Each job consists of a file to download along with it's associated
    # initial time
    job_list=[]
    for d in date_range_6h:
        download_url = cfs.forecast_url_from_timestamp(forecast_time=d,
                                                         protocal='http')
        job_list.append({'download_url':download_url, 'forecast_date':d})
    
    cfs.close()
    
    num_jobs = len(job_list)
    
    #Dole out the first round of jobs to all workers
    for i in range(1, num_workers):
        job_info = job_list.pop()
        comm.send(obj = job_info, dest=i, tag=work_tag)
    
    #While there are new jobs to assign.
    #Collect results and assign new jobs as others are finished.
    results = []
    while len(job_list)>0:
        next_job_info = job_list.pop()
        job_result = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
        results.append(job_result)
        num_finished_jobs=len(results)
        print('completed: ' +str(num_finished_jobs)+'/'+str(num_jobs) +' , ' + \
              str(job_result['forecast_date']) + ' ' + str(job_result) + ' ' + \
              str(job_result['processing_time_min']))
    
        comm.send(obj=next_job_info, dest=status.Get_source(), tag=work_tag)

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