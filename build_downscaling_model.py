import xarray as xr
import pandas as pd
import numpy as np
from scipy.stats import linregress as lm
import yaml
from tools import prism_tools, cfs_tools, tools
import os
import glob
import warnings


def collect_monthly_data(obj, month, ilat, ilon):
    obs_months = pd.DatetimeIndex(obj.time.values).month
    data_values = obj.isel(lat=ilat,lon=ilon, time=obs_months==month).tmean.values
    data_timestamps = obj.isel(lat=ilat,lon=ilon, time=obs_months==month).time.values
    
    return data_values
    
#############################################################
#############################################################
with open('config.yaml', 'r') as f:
    config = yaml.load(f)

land_mask = xr.open_dataset(config['data_folder']+config['mask_file'])

reanalysis_filenames = glob.glob(config['historic_reanalysis_folder']+'cfsv2_reanalysis*')
reanalysis_obj = xr.open_mfdataset(reanalysis_filenames)

observation_filenames = glob.glob(config['historic_observations_folder']+'yearly/prism_tmean*')
observations_obj = xr.open_mfdataset(observation_filenames)

# create a coefficient array to fill up with values
empty_array = np.ones((12, land_mask.dims['lat'], land_mask.dims['lon']))
empty_array[:] = np.nan
model_coef=xr.Dataset({'slope':(('month','lat','lon'), empty_array),
                       'intercept':(('month','lat','lon'), empty_array)},
                      {'lat':land_mask.lat.values, 'lon':land_mask.lon.values,
                       'month':np.arange(1,13)})


# Reconcile dates. A few dates are missing in the reanalysis and prism. 
# notably jan,feb,march 2011 in the reanalysis, and some dates in oct,nov 2015 for prism
# TODO: look into those.
reanalysis_keep = [time in observations_obj.time.values for time in reanalysis_obj.time.values]
observations_keep = [time in reanalysis_obj.time.values for time in observations_obj.time.values]

reanalysis_obj = reanalysis_obj.isel(time=reanalysis_keep)
observations_obj = observations_obj.isel(time=observations_keep)

assert np.all(np.equal(observations_obj.time.values, reanalysis_obj.time.values)), 'Dates not matching up'

#########################################
total_pixels = land_mask.land.values.sum()
progress=0
pixel_processing_times=[]
import time
for lat_i in range(len(land_mask.lat)):
    for lon_i in range(len(land_mask.lon)):
        is_land = land_mask.isel(lat=lat_i,lon=lon_i).land.values
        if is_land:
            pixel_start_time=time.time()
            for month_i, month in enumerate(range(1,13)):
                reanalysis = collect_monthly_data(reanalysis_obj, month=month, ilat=lat_i, ilon=lon_i)
                observations = collect_monthly_data(observations_obj, month=month, ilat=lat_i, ilon=lon_i)

                # The ranking step of the downscaling model
                reanalysis.sort()
                observations.sort()

                slope, intercept, *_ = lm(x=reanalysis, y=observations)

                model_coef['slope'][month_i, lat_i, lon_i]=slope
                model_coef['intercept'][month_i, lat_i, lon_i]=intercept

            pixel_processing_times.append(round(time.time() - pixel_start_time, 1))
            print(str(progress)+'/'+str(total_pixels)+' pixels, '+str(pixel_processing_times[-1])+' sec')
            print('avg: '+str(np.mean(pixel_processing_times)))
