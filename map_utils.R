
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

#########################################################################
# A data.frame for a specific species/phenophase with columns for
# doy_prediction and doy_sd
get_forecast_df = function(nc_object, phenophase, species, variable, downscale_factor){
  doy_prediction = raster_from_netcdf(n, phenophase = phenophase, species = species, 
                                      variable = 'doy_prediction', downscale_factor = downscale_factor) %>%
    rasterToPoints() %>%
    data.frame()
  colnames(doy_prediction) = c('lat','lon','doy_prediction')
  doy_sd = raster_from_netcdf(n, phenophase = phenophase, species = species, variable = 'doy_sd') %>%
    rasterToPoints() %>%
    data.frame()
  colnames(doy_sd) = c('lat','lon','doy_sd')
  
  full_forecast = doy_prediction %>%
    left_join(doy_sd, by=c('lat','lon'))
  
}


static_map = function(){
  
  ggplot() + 
    #geom_hex(data = species_data, aes(x=lat, y=lon, color=doy_prediction), bins=10)+
    geom_raster(data = species_data, aes(x=lat, y=lon, fill=doy_prediction)) +
    scale_fill_viridis(labels = doy_to_date) + 
    geom_polygon(data = basemap, aes(x=long, y = lat, group = group), fill=NA, color='grey20', size=0.5) + 
    coord_fixed(1.3) +
    theme_bw() + 
    guides(fill = guide_colorbar(title = 'Date of Flowering',
                                 title.position = 'top',,
                                 title.hjust = 0.5)) + 
    theme(legend.position = 'bottom',
          legend.key.width = unit(5, 'cm'),
          legend.title = element_text(size=20),
          legend.text = element_text(size=12),
          plot.title = element_text(size=22),
          plot.subtitle = element_text(size=15),
          plot.background = element_rect(fill='grey97'),
          panel.background =  element_rect(fill='grey97'),
          legend.background =  element_rect(fill='grey97'))+
    theme(axis.title = element_blank(),
          axis.text = element_blank(),
          panel.grid = element_blank(),
          axis.ticks = element_blank(),
          panel.border = element_blank())+
    labs(title = "Phenology Forecasts - Eastern redbud (Cercis canadensis) Flowers", 
         subtitle = "Predicted date of flowering for 2018 - Issued Jan 5, 2018")
  
  
  
}






