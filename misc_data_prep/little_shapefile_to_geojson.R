library(rgdal)
# This are Tree Ranges from the Little Dataset, hosted here https://github.com/wpetry/USTreeAtlas.
# These will end up in a netcdf file using python xarray, but various python packages using gdal (fiona, geopandas) 
# have trouble reading them at the moment, so this script will read them and convert to geojson for further
# processing in python

# The weird projection used in these shapefiles
#little_proj='+proj=aea +lat_1=38 +lat_2=42 +lat_0=40 +lon_0=-82 +x_0=0 +y_0=0 +ellps=clrk66 +units=m +no_defs'
data_folder = '/home/shawn/data/USTreeAtlas/'
species_list = read.csv(paste0(data_folder, 'Little_datatable.csv'))

for(i in 1:nrow(species_list)){
  species = tolower(as.character(species_list$Latin.Name[i]))
  genus = stringr::word(species,1,1)
  epithet = stringr::word(species,2,2)
  sp_code = paste0(substr(genus,1,4),substr(epithet,1,4))
  
  # This one gets mistaken for acer saccharinum
  if(species=='acer saccharum'){
    sp_code = 'acersacr'
  }
  
  if(!file.exists(paste0(data_folder,'SHP/',sp_code,'/',sp_code,'.shp'))){
    print(paste('shapefile missing ',species,':',sp_code))
    next
  }
  
  shapefile = try(readOGR(dsn=paste0(data_folder,'SHP/',sp_code),
                      layer = sp_code))
  if(class(shapefile)=='try-error'){
    print(paste('cant open',species,':',sp_code))
  }
  new_name = tolower(stringr::str_replace(species,' ','_'))
  
  writeOGR(shapefile, dsn = paste0('/home/shawn/data/phenology_forecasting/plant_ranges/',new_name), layer=new_name, driver = 'GeoJSON')
  file.rename( paste0('/home/shawn/data/phenology_forecasting/plant_ranges/',new_name),
               paste0('/home/shawn/data/phenology_forecasting/plant_ranges/',new_name,'.geojson'))
}
