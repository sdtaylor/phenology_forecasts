
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
  
  # do not need high precision for static images
  lon = round(nc_object$dim$lon$vals, 4)
  lat = round(nc_object$dim$lat$vals, 4)
  raster_obj = raster(t(data_matrix), xmn=min(lon), xmx=max(lon), ymn=min(lat), ymx=max(lat))
  
  if(!is.na(downscale_factor)){
    raster_obj = raster::aggregate(raster_obj, fact=downscale_factor)
  }
  
  return(raster_obj)
}

#########################################################################
# Set the CRS of a raster and transform to another
raster_set_change_crs = function(r, current, to){
  raster::crs(r) = current
  return(raster::projectRaster(r, crs=sp::CRS(to)))
}

#########################################################################
# A data.frame for a specific species/phenophase with columns for
# doy_prediction and doy_sd
get_forecast_df = function(nc_object, phenophase, species, downscale_factor=NA){
  # nc_crs = ncdf4::ncatt_get(nc_object, varid=0, attname='crs')$value
  # new_crs = '+init=epsg:3857'
  
  doy_prediction = raster_from_netcdf(nc_object, phenophase = phenophase, species = species, 
                                      variable = 'doy_prediction', downscale_factor = downscale_factor) %>%
    #raster_set_change_crs(current=nc_crs, to=new_crs) %>%
    rasterToPoints() %>%
    as_tibble()
  colnames(doy_prediction) = c('lat','lon','doy_prediction')
  
  doy_sd = raster_from_netcdf(nc_object, phenophase = phenophase, species = species, variable = 'doy_sd') %>%
    #raster_set_change_crs(current=nc_crs, to=new_crs) %>%
    rasterToPoints() %>%
    as_tibble()
  colnames(doy_sd) = c('lat','lon','doy_sd')
  
  full_forecast = doy_prediction %>%
    left_join(doy_sd, by=c('lat','lon'))
  
}


#################################################################
# Modified addRasterImage function from https://github.com/rstudio/leaflet
# Transform a raster to a png suitable for displaying on leaflet maps
raster_to_leaflet_image <- function(
  x,
  colors = "Spectral",
  color_domain=NULL,
  opacity = 1,
  attribution = NULL,
  layerId = NULL,
  group = NULL,
  project = TRUE,
  maxBytes = 4*1024*1024
) {
  stopifnot(inherits(x, "RasterLayer"))
  
  if (project) {
    projected <- leaflet::projectRasterForLeaflet(x)
  } else {
    projected <- x
  }
  bounds <- raster::extent(raster::projectExtent(raster::projectExtent(x, crs = sp::CRS('+init=epsg:3857')), crs = sp::CRS('+init=epsg:4326')))
  
  if (!is.function(colors)) {
    colors <- leaflet::colorNumeric(colors, domain = color_domain, na.color = "#00000000", alpha = TRUE)
  }
  
  tileData <- raster::values(projected) %>% colors() %>% col2rgb(alpha = TRUE) %>% as.raw()
  dim(tileData) <- c(4, ncol(projected), nrow(projected))
  #pngData <- png::writePNG(tileData)

  return(tileData)
  # latlng <- list(
  #   list(raster::ymax(bounds), raster::xmin(bounds)),
  #   list(raster::ymin(bounds), raster::xmax(bounds))
  # )
}
