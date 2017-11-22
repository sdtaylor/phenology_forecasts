# This is for download large amounts of historic forecasts and observations
# for making the downscaling models. By large I mean like 20 years

import xarray as xr
import pandas as pd
import yaml
from tools import prism_tools, cfs_tools, tools


with open('config.yaml', 'r') as f:
    config = yaml.load(f)

####################
# CFS historic forecasts
####################

# Collect information on available CFS forecasts
begin_date = tools.string_to_date(str(config['historic_years_begin'])+'0101', h=False)
end_date = tools.string_to_date(str(config['historic_years_end'])+'0231', h=False)

# CFS has forecasts every 6 hours
date_range_6h = pd.date_range(begin_date, end_date, freq='6H').to_pydatetime()

cfs = cfs_tools.cfs_ftp_info()

# Check which ones are available. After 2011 they are available every day,
# every 6 hours. But reforecasts from 1982-2010 are only every 5th day
date_range_6h = [d for d in date_range_6h if cfs.forecast_available(d)]

    
land_mask = xr.open_dataset(config['data_folder']+config['mask_file'])
tmean_names = config['variables_to_use']['tmean']

for d in date_range_6h:
    forecast_obj = cfs_tools.download_and_process_forecast(cfs_info = cfs,
                                                           date=d,
                                                           target_downscale_array=land_mask.to_array()[0])
    
    processed_filename = config['data_folder']+'cfsv2_'+tools.date_to_string(d,h=True)+'.nc'
    forecast_obj.to_netcdf(processed_filename)


cfs.close()

###################
# PRISM historic data
##################

prism = prism_tools.prism_ftp_info()

date_range_daily = pd.date_range(begin_date, end_date, freq='1D').to_pydatetime()

# All dates for PRISM should be available, but check just to make sure
date_range_daily = [d for d in date_range_daily if prism.date_available(d)]

for i, d in enumerate(date_range_daily):
    d_array = prism_tools.download_and_process_day(prism_info=prism, date=d,
                                                varname='tmean', 
                                                status=prism.get_date_status(d))
    if i==0:
        final_array = d_array
    else:
        final_array = final_array.combine_first(d_array)

final_array.to_netcdf(config['historic_observations_file'])

prism.close()




