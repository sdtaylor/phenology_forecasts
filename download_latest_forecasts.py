import xarray as xr
import yaml
import os
import urllib
from tools import cfs_tools
from tools import tools


if __name__=='__main__':
    with open('config.yaml', 'r') as f:
        config = yaml.load(f)
    cfs = cfs_tools.cfs_ftp_info()
    
    land_mask = xr.open_dataset(config['data_folder']+config['mask_file'])
    tmean_names = config['variables_to_use']['tmean']
    
    for forecast_info in cfs.last_n_forecasts(n=10)[1:3]:
        #forecast_info = {'download_url':'/home/shawn/data/phenology_forecasting/tmp2m.01.2017111218.daily.grb2',
        #                 'initial_time':'2017111218'}
        forecast_filename = config['tmp_folder']+ os.path.basename(forecast_info['download_url'])
        urllib.request.urlretrieve(forecast_info['download_url'], forecast_filename)

        # Dowload forecast file
        #forecast_filename = forecast_info['download_url']
    
        forecast_obj = cfs_tools.open_cfs_forecast(forecast_filename)
        initial_time= tools.string_to_date(forecast_info['initial_time'], hour=True)
        
        # More reasonable variable names
        forecast_obj.rename({'lat_0':'lat', 'lon_0':'lon', 
                             'forecast_time0':'forecast_time',
                             tmean_names['cfs_nc_name']:'tmean'}, inplace=True)
    
        # Kelvin to celcius
        forecast_obj['tmean'] -= 273.15
        
        # 6 hourly timesteps to daily timesteps
        forecast_obj = cfs_tools.cfs_to_daily_mean(cfs=forecast_obj, cfs_initial_time = initial_time)
    
        # ~1.0 deg cfs grid to 4km prism grid.
        forecast_obj = cfs_tools.spatial_downscale(ds = forecast_obj, target_array = land_mask.to_array()[0])
        
        processed_filename = config['data_folder']+'cfsv2_'+forecast_info['initial_time']+'.nc'
        forecast_obj.to_netcdf(processed_filename)
        # forecast_obj = statistical_downscale(forecast_obj)
    
    cfs.close()