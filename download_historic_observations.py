# This is for download large amounts of historic forecasts and observations
# for making the downscaling models. By large I mean like 20 years

import xarray as xr
import pandas as pd
import yaml
from tools import prism_tools, cfs_tools, tools


with open('config.yaml', 'r') as f:
    config = yaml.load(f)

###################
# PRISM historic data
##################

begin_date = tools.string_to_date(str(config['historic_years_begin'])+'0101', h=False)
end_date = tools.string_to_date(str(config['historic_years_end'])+'1231', h=False)

prism = prism_tools.prism_ftp_info()

date_range_daily = pd.date_range(begin_date, end_date, freq='1D').to_pydatetime()

# All dates for PRISM should be available, but check just to make sure
date_range_daily = [d for d in date_range_daily if prism.date_available(d)]

num_files = len(date_range_daily)

for i, d in enumerate(date_range_daily):
    d_array = prism_tools.download_and_process_day(prism_info=prism, date=d,
                                                varname='tmean', 
                                                status=prism.get_date_status(d))
    if i==0:
        final_array = d_array
    else:
        final_array = final_array.combine_first(d_array)

    print(str(i)+' of '+str(num_files))
    tools.cleanup_tmp_folder(config['tmp_folder'])

final_array.to_netcdf(config['historic_observations_file'], encoding={'tmean': {'zlib':True,'complevel':4,'shuffle':True}})

prism.close()



