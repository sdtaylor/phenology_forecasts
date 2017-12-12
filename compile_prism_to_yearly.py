import yaml
import xarray as xr

# TODO: add this into download_historic_observations.py

with open('config.yaml', 'r') as f:
    config = yaml.load(f)

for year in range(config['historic_years_begin'], config['historic_years_end']+1):
    print(year)
    search_path = config['historic_observations_folder']+'prism_tmean_'+str(year)+'*'
    this_year_observations = xr.open_mfdataset(search_path)
    
    year_filename = config['historic_observations_folder'] + 'yearly/'+'prism_tmean_'+str(year)+'.nc'
    
    time_dims = len(this_year_observations.time)
    this_year_observations.to_netcdf(year_filename, encoding={'tmean':{'zlib':True, 
                                                                       'complevel':1, 
                                                                       'chunksizes':(10,10,time_dims)}})