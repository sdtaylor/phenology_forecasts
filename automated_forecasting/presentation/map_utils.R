
###########################################################################
# Pull a specific raster out of a netcdf file
raster_from_netcdf = function(nc_object, phenophase, species, variable, downscale_factor=NA){
  phenophase_index = base::match(phenophase, nc_object$dim$phenophase$vals)
  species_index    = base::match(species, nc_object$dim$species$vals)
  
  if(is.na(phenophase_index)) stop('phenophase not found')
  if(is.na(species_index)) stop('species not found')
  
  # Thanks https://stackoverflow.com/a/22944715
  start = c(lat = 1, lon = 1, phenophase = phenophase_index, species = species_index)
  count = c(lat = -1, lon = -1, phenophase = 1, species = 1)
  dim_order = sapply(nc_object$var[[variable]]$dim, function(x) x$name)
  
  data_matrix = ncvar_get(nc_object, varid=variable, start = start[dim_order], count = count[dim_order])
  
  lon = nc_object$dim$lon$vals
  lat = nc_object$dim$lat$vals
  raster_obj = raster(t(data_matrix), xmn=min(lon), xmx=max(lon), ymn=min(lat), ymx=max(lat))
  
  if(!is.na(downscale_factor)){
    raster_obj = raster::aggregate(raster_obj, fact=downscale_factor)
  }
  
  return(raster_obj)
}

#######################################################################
# Get the current growing season. ie. 2018 for all dates 2017-11-1 to 2018-10-30
current_growing_season = function(){
  config=load_config()
  today = Sys.Date()
  year = lubridate::year(today)
  season_begin = as.Date(paste(year,config$season_month_begin,config$season_day_begin,sep='-'))
  if(today > season_begin){
    year = year+1
  }
  return(year)
}

#########################################################################
# Take doy of the current season and return Mar. 1, Jan. 30, etc.
doy_to_date = function(x){
  current_season = current_growing_season()
  dates = as_date(paste(current_season, x,sep='-'), '%Y-%j')
  abbr  = strftime(dates, '%b %d')
  return(abbr)
}

#########################################################################
# A data.frame for a specific species/phenophase with columns for
# doy_prediction and doy_sd
get_forecast_df = function(nc_object, phenophase, species, downscale_factor=NA){
  doy_prediction = raster_from_netcdf(nc_object, phenophase = phenophase, species = species, 
                                      variable = 'doy_prediction', downscale_factor = downscale_factor) %>%
    rasterToPoints() %>%
    data.frame()
  colnames(doy_prediction) = c('lat','lon','doy_prediction')
  doy_sd = raster_from_netcdf(nc_object, phenophase = phenophase, species = species, variable = 'doy_sd') %>%
    rasterToPoints() %>%
    data.frame()
  colnames(doy_sd) = c('lat','lon','doy_sd')
  
  full_forecast = doy_prediction %>%
    left_join(doy_sd, by=c('lat','lon'))
  
}

###################################################################
# Prepend the root data folder to all files and folders
# specified. 
load_config = function(){
  config = yaml::yaml.load_file('config.yaml')
  
  data_folder = config$data_folder
  
  config_attributes = names(config)
  # Don't prepend the root data_folder
  config_attributes = config_attributes[-which('data_folder' %in% config_attributes)]
  
  for(a in config_attributes){
    is_dir = grepl('folder',a)
    is_file= grepl('file',a)
    if(is_dir | is_file){
      config[[a]] = paste0(data_folder,config[[a]])
    }
    if(is_dir){
      if(!dir.exists(config[[a]])) dir.create(config[[a]])
    }
  }
  return(config)
}

###################################################################
#Appending a csv without re-writing the header.
append_csv=function(df, filename){
  write.table(df, filename, sep = ',', row.names = FALSE, col.names = !file.exists(filename), append = file.exists(filename))
}
