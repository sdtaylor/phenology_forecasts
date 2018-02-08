import xarray as xr
import pandas as pd
import numpy as np
from scipy.stats import linregress as lm
from tools import prism_tools, cfs_tools, tools
import os
import glob
import warnings

#TODO: 
# Optimize this so it doesn't use a bunch of for loops
#   probably using xr.apply_ufunc()
# Compress the final file to get it as small as possible.
#   and saved on github or shared with others

def collect_monthly_data(obj, ilat, ilon):
    obj_months = pd.DatetimeIndex(obj.time.values).month
    data_values = obj.isel(lat=ilat,lon=ilon).tmean.values
    #data_timestamps = obj.isel(lat=ilat,lon=ilon, time=obs_months==month).time.values
    
    return data_values, obj_months
    
#############################################################
#############################################################
config = tools.load_config()

land_mask = xr.open_dataset(config['mask_file'])

reanalysis_filenames = glob.glob(config['historic_reanalysis_folder']+'cfsv2_reanalysis*')
reanalysis_obj = xr.open_mfdataset(reanalysis_filenames, chunks={'lat':10, 'lon':10})

observation_filenames = glob.glob(config['historic_observations_folder']+'yearly/prism_tmean*')
observations_obj = xr.open_mfdataset(observation_filenames, chunks={'lat':10, 'lon':10})

# create a coefficient array to fill up with values
empty_array = np.ones((12, land_mask.dims['lat'], land_mask.dims['lon']))
empty_array[:] = np.nan
model_coef=xr.Dataset({'slope':(('month','lat','lon'), empty_array.copy()),
                       'intercept':(('month','lat','lon'), empty_array.copy())},
                      {'lat':land_mask.lat.values, 'lon':land_mask.lon.values,
                       'month':np.arange(1,13)})


# Reconcile dates. A few dates are missing in the reanalysis and prism. 
# notably jan,feb,march 2011 in the reanalysis, and some dates in oct,nov 2015 for prism
# TODO: look into those.
reanalysis_keep = [time in observations_obj.time.values for time in reanalysis_obj.time.values]
observations_keep = [time in reanalysis_obj.time.values for time in observations_obj.time.values]

#reanalysis_obj = reanalysis_obj.isel(time=reanalysis_keep).sortby('time')
#observations_obj = observations_obj.isel(time=observations_keep).sortby('time')
reanalysis_obj = reanalysis_obj.isel(time=reanalysis_keep)
observations_obj = observations_obj.isel(time=observations_keep)

#assert np.all(np.equal(observations_obj.time.values, reanalysis_obj.time.values)), 'Dates not matching up'

#########################################
# Get a list of chunks of size:size, with any leftover
# elements in the final chunk
def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))
########################################
total_pixels = land_mask.land.values.sum()
progress=0
pixel_processing_times=[]
import time
lat_lon_chunk=10

# Iterate over specific chunks of the data, then within each chunk
# load all data inter memory and iterate over specific spatial cells.
# This could probably be improved, but it's fairly quick and memory
# friendly. 

for lat_chunk in list(chunker(land_mask.lat, lat_lon_chunk)):
    for lon_chunk in list(chunker(land_mask.lon, lat_lon_chunk)):
        land_mask_subset = land_mask.sel(lat=lat_chunk, lon=lon_chunk)
        if np.all(~land_mask_subset.land.values):
            continue
       
        print('chunking')
        reanalysis_subset = reanalysis_obj.sel(lat=lat_chunk, lon=lon_chunk)
        observations_subset = observations_obj.sel(lat=lat_chunk, lon=lon_chunk)

        print('loading re')
        reanalysis_subset.load()
        print('loading obs')
        observations_subset.load()
        land_mask_subset.load()
    
        print(len(land_mask_subset.lat))
        for lat_i in range(len(land_mask_subset.lat)):
            for lon_i in range(len(land_mask_subset.lon)):
                is_land = land_mask_subset.isel(lat=lat_i,lon=lon_i).land.values
                if is_land:
                    pixel_start_time=time.time()
                    print('collecting')
        
                    reanalysis_data, reanalysis_months = collect_monthly_data(reanalysis_subset, ilat=lat_i, ilon=lon_i)
                    observations_data, observations_months = collect_monthly_data(observations_subset, ilat=lat_i, ilon=lon_i)
        
                    for month_i, month in enumerate(range(1,13)):
                        #print('month: '+str(month))
                        reanalysis = reanalysis_data[reanalysis_months==month].copy()
                        observations = observations_data[observations_months==month].copy()
        
                        # The ranking step of the downscaling model
                        reanalysis.sort()
                        observations.sort()
                        
                        slope, intercept, *_ = lm(x=reanalysis, y=observations)
                        #print(slope)
                        #print(intercept)
        
                        full_array_lat_i = np.where(land_mask.lat.values == land_mask_subset.lat.values[lat_i])[0][0]
                        full_array_lon_i = np.where(land_mask.lon.values == land_mask_subset.lon.values[lon_i])[0][0]
                        model_coef['slope'][month_i, full_array_lat_i, full_array_lon_i]=slope
                        model_coef['intercept'][month_i, full_array_lat_i, full_array_lon_i]=intercept
        
                    progress+=1
                    pixel_processing_times.append(round(time.time() - pixel_start_time, 1))
                    print(str(progress)+'/'+str(total_pixels)+' pixels, '+str(pixel_processing_times[-1])+' sec')
                    print('avg: '+str(np.mean(pixel_processing_times)))

        #model_coef = model_coef.update(model_coef_subset).copy()
        #print(model_coef_subset.slope.shape)
        #print('subset slope num nan: '+str(np.sum(~np.isnan(model_coef_subset.slope))))
        #print('subset intercept num nan: '+str(np.sum(~np.isnan(model_coef_subset.intercept))))
        print('original slope num nan: '+str(np.sum(~np.isnan(model_coef.slope))))
        print('original intercpet num nan: '+str(np.sum(~np.isnan(model_coef.intercept))))

model_coef.to_netcdf(config['downscaling_model_coefficients_file'], 
                     encoding={'slope':    {'zlib':True,'complevel':9, 'dtype':'int32', 'scale_factor':0.00001,  '_FillValue': -99999}, 
                               'intercept':{'zlib':True,'complevel':9, 'dtype':'int32', 'scale_factor':0.00001,  '_FillValue': -99999}})
