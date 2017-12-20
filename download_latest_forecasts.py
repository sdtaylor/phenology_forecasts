import xarray as xr
import pandas as pd
import numpy as np
import os
from tools import cfs_tools
from tools import tools
import datetime


def broadcast_downscale_model(model, start_date, end_date, verbose=True):
    """The downscaling model netcdf has, for every pixel and
    every calendar month, a slope and intercept to apply to 
    downscale with. This broadcasts it to a full date range
    to make for very easy application of it.
    """
    
    # Note, need to make this pretty wide  to apply to ~10 forcasts
    # with different lead times. Or do I? the forecats will already be
    # cropped to the correct today - end_date, so no. 
    date_range = pd.date_range(start_date, end_date)
    model_broadcasted = model.sel(month = [date_range[0].month]).copy()
    model_broadcasted = model_broadcasted.rename({'month':'time'})
    model_broadcasted['time'] = [date_range[0]]
    
    for count, date in enumerate(date_range[1:]):
        day_broadcast = model.sel(month = [date.month]).copy()
        day_broadcast = day_broadcast.rename({'month':'time'})
        day_broadcast['time'] = [date]
        model_broadcasted = xr.merge([model_broadcasted, day_broadcast]).copy()
        if verbose and count % 10 == 0:
            print('Broadcasting downscale model progress: {x} of {y}'.format(x=count,y=len(date_range)))
    
    #TODO: This take up a lot of memory. Need to write it to disk in the tmp
    # folder and open it with xarray chunks.
    return model_broadcasted


def main():
    config = tools.load_config()
    
    land_mask = xr.open_dataset(config['mask_file'])
    tmean_names = config['variables_to_use']['tmean']
    
    max_lead_time_weeks = 2
    
    today = pd.Timestamp.today().date()
    end_date = today + pd.offsets.Week(max_lead_time_weeks)
        
    downscale_model = xr.open_dataset(config['downscaling_model_coefficients_file'])
    downscale_model = broadcast_downscale_model(downscale_model,
                                                start_date=today,
                                                end_date=end_date)
    
    downscale_model = downscale_model.chunk({'lat':20,'lon':20})
    
    # The weather up until today
    current_season_observed = xr.open_dataset(config['current_season_observations_file'])
    
    cfs = cfs_tools.cfs_ftp_info()
    most_recent_forecasts = cfs.last_n_forecasts(n=1)
    cfs.close()
    
    for forecast_info in most_recent_forecasts:
        local_filename = config['tmp_folder']+ os.path.basename(forecast_info['download_url'])
        print(local_filename)
        print(forecast_info['download_url'])
        tools.download_file(forecast_info['download_url'], local_filename)

        initial_time= tools.string_to_date(forecast_info['initial_time'], h=True)


        forecast_obj = cfs_tools.convert_cfs_grib_forecast(local_filename,
                                                           add_initial_time_dim=False,
                                                           date = initial_time)
        
        # ~1.0 deg cfs grid to 4km prism grid.
        #TODO: use distance_weighted method with k:2
        forecast_obj = cfs_tools.spatial_downscale(ds = forecast_obj, 
                                                   method='nearest',
                                                   downscale_args={'k':1},
                                                   data_var='tmean',
                                                   target_array = land_mask.to_array()[0])
        
        # Limit to the lead time. 
        dates_after_today = forecast_obj.forecast_time.values >= np.datetime64(today)
        dates_before_end =  forecast_obj.forecast_time.values <= np.datetime64(end_date)
        times_to_keep = np.logical_and(dates_after_today, dates_before_end)
        forecast_obj = forecast_obj.isel(forecast_time = times_to_keep)
        
        # Apply downscaling model
        print(forecast_obj)
        print(downscale_model)
        forecast_obj = forecast_obj.rename({'forecast_time':'time'})
        forecast_obj = forecast_obj.chunk({'lat':20,'lon':20})
        
        forecast_obj = forecast_obj['tmean'] * downscale_model.slope + downscale_model.intercept
        forecast_obj = forecast_obj.to_dataset(name='tmean')
        
        # Add in observed observations
        forecast_obj = xr.merge([forecast_obj, current_season_observed])
        
        # TODO: add provenance metadata
        
        processed_filename = config['current_forecast_folder']+'cfsv2_'+forecast_info['initial_time']+'.nc'
        forecast_obj.to_netcdf(processed_filename)


if __name__=='__main__':
    main()
