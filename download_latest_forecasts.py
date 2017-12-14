import xarray as xr
import yaml
import os
from tools import cfs_tools
from tools import tools


if __name__=='__main__':
    with open('config.yaml', 'r') as f:
        config = yaml.load(f)
    cfs = cfs_tools.cfs_ftp_info()
    
    land_mask = xr.open_dataset(config['data_folder']+config['mask_file'])
    tmean_names = config['variables_to_use']['tmean']
    
    # TODO: download all of them
    for forecast_info in cfs.last_n_forecasts(n=1):
        local_filename = config['tmp_folder']+ os.path.basename(forecast_info['download_url'])
        print(local_filename)
        print(forecast_info['download_url'])
        tools.download_file(forecast_info['download_url'], local_filename)

        initial_time= tools.string_to_date(forecast_info['initial_time'], h=True)


        forecast_obj = cfs_tools.process_forecast(local_filename,
                                                  date = initial_time,
                                                  target_downscale_array=land_mask.to_array()[0])
        
        processed_filename = config['data_folder']+'cfsv2_'+forecast_info['initial_time']+'.nc'
        forecast_obj.to_netcdf(processed_filename)
 
    cfs.close()