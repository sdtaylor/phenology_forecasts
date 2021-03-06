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

def get_forecasts_from_date(forecast_date, destination_folder,
                            lead_time = 36, forecast_ensemble_size=5,
                            current_season_observed=None):
    """Download and process forecasts from a specific date
    
    
    In the daily forecasting the date will be "today", but in hindcasting
    will be dates in the  past. In which case it will obtain n forecasts 
    starting on the 18 hour of the forecast date and working backword in 
    time. n being equal to forecast_ensemble_size.
    
    ie. forecast_date = '20180215' will get forecasts at 
    ['2018021518','2018021512','2018021506','2018021500','2018021418']
    or more prior ones if <5 are available. 
    
    current_season_observed
        xarray object of one produced by download_latest_observations
    """
    config = tools.load_config()
    
    if not current_season_observed:
        current_season_observed = xr.open_dataset(config['current_season_observations_file'])
    current_season_observed = current_season_observed.drop('status')
    
    land_mask = xr.open_dataset(config['mask_file'])
    tmean_names = config['variables_to_use']['tmean']
    
    most_recent_observed_day = pd.Timestamp(current_season_observed.time.values[-1]).to_pydatetime()
    first_forecast_day = most_recent_observed_day + datetime.timedelta(days=1)

    #today = pd.Timestamp.today().date()
    last_forecast_day = forecast_date + pd.offsets.Week(lead_time)
    
    # Get info for more forecasts than needed in case some fail
    # during processing. 4 forecasts are issued every day, so 10
    # extra is about 2 days worth. 
    cfs = cfs_tools.cfs_ftp_info()
    most_recent_forecasts = cfs.last_n_forecasts(n=forecast_ensemble_size + 20,
                                                 from_date=forecast_date)
    cfs.close()
    
    # Arrange the downscale model to easily do array math with the 
    # forecast arrays. And chunk it so it doesn't consume a large
    # memory footprint (but takes a few minutes longer)
    downscale_model = xr.open_dataset(config['downscaling_model_coefficients_file'])
    downscale_model.load()
    downscale_model = broadcast_downscale_model(downscale_model,
                                                start_date=first_forecast_day,
                                                end_date=last_forecast_day)
    downscale_model = downscale_model.chunk({'lat':200,'lon':200})
    
    num_forecasts_added = 0
    print(len(most_recent_forecasts))
    for forecast_info in most_recent_forecasts:
        if num_forecasts_added == forecast_ensemble_size:
            break
        
        local_filename = config['tmp_folder']+ os.path.basename(forecast_info['download_url'])
        initial_time= tools.string_to_date(forecast_info['initial_time'], h=True)
        
        print('\n\n\n')
        print('Attempting to process climate forecast {i} of {n} with initial time {t}'.format(i=num_forecasts_added,
                                                                                       n=forecast_ensemble_size,
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
        
        # If the last day of the CFS forecast is off a lot a bunch from the
        # last day we're shooting for skip it. This happens occasionaly cause of
        # I'm assuming, errors on NOAA's end
        if forecast_obj.forecast_time[-1].values < np.datetime64(last_forecast_day):
            print('Skipping due to bad forecast end date. ends on {d}'.format(d=forecast_obj.forecast_time[-1].values))
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
            forecast_obj = forecast_obj.chunk({'lat':200,'lon':200})
            
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
            processed_filename = destination_folder+'cfsv2_'+forecast_info['initial_time']+'.nc'
            forecast_obj.to_netcdf(processed_filename)
        except:
            print('processing error in saving file')
            continue
        
        print('Successfuly proccessed forecast from initial time: '+str(initial_time))
        num_forecasts_added+=1

    assert num_forecasts_added==forecast_ensemble_size, 'not enough forecasts added. {added} of {needed}'.format(added=num_forecasts_added, 
                                                                                                              needed=forecast_ensemble_size)
