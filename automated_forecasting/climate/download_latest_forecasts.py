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
    
    return model_broadcasted

def run():
    config = tools.load_config()
    
    land_mask = xr.open_dataset(config['mask_file'])
    tmean_names = config['variables_to_use']['tmean']
    
    # The weather up until today. This accounts for PRISM potentially not being
    # updated to the most recent day (ie. yesterday). 
    current_season_observed = xr.open_dataset(config['current_season_observations_file'])
    most_recent_observed_day = pd.Timestamp(current_season_observed.time.values[-1]).to_pydatetime()
    first_forecast_day = most_recent_observed_day + datetime.timedelta(days=1)
    
    max_lead_time_weeks = 32
    forecast_ensemble_n = 5
    
    today = pd.Timestamp.today().date()
    last_forecast_day = today + pd.offsets.Week(max_lead_time_weeks)
    
    # Get info for more forecasts than needed in case some fail
    # during processing. 4 forecasts are issued every day, so 10
    # extra is about 2 days worth. 
    cfs = cfs_tools.cfs_ftp_info()
    most_recent_forecasts = cfs.last_n_forecasts(n=forecast_ensemble_n + 10)
    cfs.close()
    
    # Arrange the downscale model to easily do array math with the 
    # forecast arrays. And chunk it so it doesn't consume a large
    # memory footprint (but takes a few minutes longer)
    downscale_model = xr.open_dataset(config['downscaling_model_coefficients_file'])
    downscale_model.load()
    downscale_model = broadcast_downscale_model(downscale_model,
                                                start_date=first_forecast_day,
                                                end_date=last_forecast_day)
    downscale_model = downscale_model.chunk({'lat':20,'lon':20})
    
    num_forecasts_added = 0
    print(len(most_recent_forecasts))
    for forecast_info in most_recent_forecasts:
        if num_forecasts_added == forecast_ensemble_n:
            break
        
        local_filename = config['tmp_folder']+ os.path.basename(forecast_info['download_url'])
        initial_time= tools.string_to_date(forecast_info['initial_time'], h=True)
        
        print('\n\n\n')
        print('Attempting to process climate forecast {i} of {n} with initial time {t}'.format(i=num_forecasts_added,
                                                                                       n=forecast_ensemble_n,
                                                                                       t = initial_time))
        print('download URL: ' + str(forecast_info['download_url']))

        # If the observed data is late in updating and the forecast
        # is very recent there will be gaps.
        if initial_time.date() > first_forecast_day.date(): 
            print('''Forecast skipped
                     Gap between forecast and observed dates
                     forecast initial time: {f_time}
                     latest observed time: {o_time}
                  '''.format(f_time=initial_time, o_time=first_forecast_day))
            continue
    
        try:
            tools.download_file(forecast_info['download_url'], local_filename)
            forecast_obj = cfs_tools.convert_cfs_grib_forecast(local_filename,
                                                               add_initial_time_dim=False,
                                                               date = initial_time)
        except:
            print('processing error in download/converting')
            continue
        
        # ~1.0 deg cfs grid to 4km prism grid.
        #TODO: use distance_weighted method with k:2
        try:
            forecast_obj = cfs_tools.spatial_downscale(ds = forecast_obj, 
                                                       method='distance_weighted',
                                                       downscale_args={'k':2},
                                                       data_var='tmean',
                                                       target_array = land_mask.to_array()[0])
        except:
            print('processing error in spatial downscale')
            continue
        
        # Limit to the lead time. 
        try:
            dates_GE_first_day = forecast_obj.forecast_time.values >= np.datetime64(first_forecast_day)
            dates_LE_last_day =  forecast_obj.forecast_time.values <= np.datetime64(last_forecast_day)
            times_to_keep = np.logical_and(dates_GE_first_day, dates_LE_last_day)
            forecast_obj = forecast_obj.isel(forecast_time = times_to_keep)
            
            # Apply downscaling model
            forecast_obj = forecast_obj.rename({'forecast_time':'time'})
            forecast_obj = forecast_obj.chunk({'lat':20,'lon':20})
            
            forecast_obj = forecast_obj['tmean'] * downscale_model.slope + downscale_model.intercept
            forecast_obj = forecast_obj.to_dataset(name='tmean')
        except:
            print('processing error in downscaling')
            continue
        
        # Add in observed observations
        # rounding errors can make it so lat/lon don't line up exactly
        # copying lat and lon fixes this.
        try:
            forecast_obj['lat'] = current_season_observed['lat']
            forecast_obj['lon'] = current_season_observed['lon']
            forecast_obj = xr.merge([forecast_obj, current_season_observed])
        except:
            print('processing error in merging with observed data')
            continue
        
        # TODO: add provenance metadata
        try:
            processed_filename = config['current_forecast_folder']+'cfsv2_'+forecast_info['initial_time']+'.nc'
            forecast_obj.to_netcdf(processed_filename)
        except:
            print('processing error in saving file')
            continue
        
        print('Successfuly proccessed forecast from initial time: '+str(initial_time))
        num_forecasts_added+=1

    assert num_forecasts_added==forecast_ensemble_n, 'not enough forecasts added. {added} of {needed}'.format(added=num_forecasts_added, 
                                                                                                              needed=forecast_ensemble_n)
    
if __name__=='__main__':
    run()()
