import xarray as xr
from rasterio import features
import rasterio
import geopandas as gpd
import fiona
import os, glob
# Create the north american land mask from a prism file
import numpy as np
from tools import prism_tools
from tools import tools

# The weird projection used in these USGS shapefiles
little_proj='+proj=aea +lat_1=38 +lat_2=42 +lat_0=40 +lon_0=-82 +x_0=0 +y_0=0 +ellps=clrk66 +units=m +no_defs'

# Run the r script to download, unzip, and write to geojson

config = tools.load_config()

# Get a prism file for reference of the crs, bounds, etc
prism = prism_tools.prism_ftp_info()
prism_date = tools.string_to_date('20100101')
prism_url = prism.get_download_url(prism_date)
prism.close()
prism_xarray = prism_tools.download_and_process_day(prism_url, prism_date,
                                      varname='tmean',status='stable')

local_prism_file = config['tmp_folder'] + os.path.basename(prism_url)
local_prism_file = local_prism_file.split('.')[0]+'.bil'

prism_raster = rasterio.open(local_prism_file)

geojson_files = glob.glob(config['data_folder']+'plant_ranges/*geojson')
species_names = []
# an array of (n_species x lat x lon)
species_masks = np.empty((len(geojson_files), len(prism_xarray.lat), len(prism_xarray.lon)))

for i, f in enumerate(geojson_files):
    obj = gpd.GeoDataFrame.from_file(f)
    obj.crs = fiona.crs.from_string(little_proj)
    obj = obj.to_crs(prism_raster.crs)
    polys=[p['geometry'] for p in obj.iterfeatures()]
    
    species_masks[i] = rasterio.features.geometry_mask(polys, 
                                                 out_shape=prism_raster.shape,
                                                 transform=prism_raster.affine,
                                                 all_touched=True,
                                                 invert=True)
    
    this_species = os.path.basename(f).split('.')[0]
    species_names.append(this_species)
    
species_range_dataset = xr.Dataset(data_vars = {'range': (('species','lat','lon'), species_masks)},
                        coords =    {'species':species_names,'lat':prism_xarray.lat, 'lon':prism_xarray.lon},
                        attrs =     {'crs':prism_xarray.crs})

species_range_dataset.to_netcdf(config['species_range_file'])

