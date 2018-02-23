library(tidyverse)
library(raster)
library(viridis)
library(ncdf4)
library(lubridate)
#library(leaflet)
source('automated_forecasting/presentation/map_utils.R')

config = load_config()

current_season=current_growing_season()

#########################################################################
# Take doy of the current season and return Mar. 1, Jan. 30, etc.
doy_to_date = function(x){
  dates = as.Date(paste(current_season, x,sep='-'), '%Y-%j')
  abbr  = strftime(dates, '%b %d')
  return(abbr)
}

###################################################
# capitilize the first letter of a string. 
capitilize = function(s){
  l = toupper(substr(s, 1,1))
  return(paste0(l,substr(s,2,nchar(s))))
}
####################################################

args=commandArgs(trailingOnly = TRUE)
phenology_forecast_filename = args[1]
phenology_forecast_filename = '/home/shawn/data/phenology_forecasting/phenology_forecasts/phenocam_phenology_forecast_2018-02-23.nc'
phenocam_forecast = ncdf4::nc_open(phenology_forecast_filename)

crs_used = ncdf4::ncatt_get(phenocam_forecast, varid=0, attname='crs')$value

issue_date = ncdf4::ncatt_get(phenocam_forecast, varid = 0, attname='issue_date')$value
# create string like Jan. 3, 2018
issue_date_abbr = strftime(as.Date(issue_date), '%b %d, %Y')

issue_date_forecast_folder = paste0(config$phenology_forecast_figure_folder,issue_date,'/')
dir.create(issue_date_forecast_folder, showWarnings = FALSE)

available_models = phenocam_forecast$dim$model$vals

image_metadata=data.frame()

basemap = map_data('state')
########################################
#color_scheme = c('blue','green1','green4','red','yellow','cyan')
# This one is hopefully somewhat colorblind friendly. RGB-Hex is the same as the names
# from: https://web.njit.edu/~kevin/rgb.txt.html
#color_scheme = c('87CEEB','9AFF9A','548B54','FF6347','FFFF00','0000FF')
prediction_color_scheme = c('skyblue','palegreen1','palegreen4','tomato','yellow','blue')

########################################
# Put the color bar labels on the 15th of every month
is_leap_year = ((current_season - 2000) %% 4 == 0)
if(is_leap_year){
  legend_label_breaks =c(15,46,75,106,136,167,197,228,259,289,320,350)
} else {
  legend_label_breaks =c(15,46,74,105,135,166,196,227,258,288,319,349)
}

uncertainty_legend_breaks = c(1,10,20,30)
uncertainty_legend_labels = c(1,10,20,'30+')
########################################
attribution_text_main="phenology.naturecast.org"
attribution_text_data="
Made with data from:
Phenocam Network
NOAA (noaa.org)
PRISM Climate Group (prism.oregonstate.edu)"

#######################################
static_image_base_plot = ggplot() + 
  #geom_hex(data = species_data, aes(x=lat, y=lon, color=doy_prediction), bins=10)+
  #geom_raster(data = raster_df, aes(x=lat, y=lon, fill=doy_sd)) +
  #geom_polygon(data = basemap, aes(x=long, y = lat, group = group), fill=NA, color='grey20', size=0.3) + 
  #scale_fill_distiller(palette='YlGnBu', direction = 1) +
  coord_fixed(1.3) +
  annotate('text',x=-125,y=28,label=attribution_text_main, size=2.8, hjust=0) +
  annotate('text',x=-125,y=26,label=attribution_text_data, size=1.8, hjust=0) +
  theme_bw() + 
  guides(fill = guide_colorbar(title.position = 'top',
                               title.hjust = 0.5)) + 
  theme(legend.position = 'bottom',
        legend.key.height = unit(0.4, 'cm'),
        legend.title = element_text(size=10),
        legend.text = element_text(size=6),
        plot.title = element_text(size=13),
        plot.subtitle = element_text(size=9),
        plot.background = element_rect(fill='grey97'),
        panel.background =  element_rect(fill='grey97'),
        legend.background =  element_rect(fill='grey97'))+
  theme(axis.title = element_blank(),
        axis.text = element_blank(),
        panel.grid = element_blank(),
        axis.ticks = element_blank(),
        panel.border = element_blank())

########################################
phenocam_raster_from_netcdf = function(nc_object, model_name, variable, downscale_factor=NA){
  model_index = base::match(model_name, nc_object$dim$model$vals)

  if(is.na(model_index)) stop('model not found')
  
  # Thanks https://stackoverflow.com/a/22944715
  start = c(lat = 1, lon = 1, model = model_index)
  count = c(lat = -1, lon = -1, model = 1)
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

get_phenocam_forecast_df = function(nc_object, model_name, downscale_factor=NA){
  doy_prediction = phenocam_raster_from_netcdf(nc_object, model_name=model_name,
                                      variable = 'doy_prediction', downscale_factor = downscale_factor) %>%
    rasterToPoints() %>%
    data.frame()
  colnames(doy_prediction) = c('lat','lon','doy_prediction')
  
  doy_sd = phenocam_raster_from_netcdf(nc_object, model_name=model_name, variable = 'doy_sd') %>%
    rasterToPoints() %>%
    data.frame()
  colnames(doy_sd) = c('lat','lon','doy_sd')
  
  full_forecast = doy_prediction %>%
    left_join(doy_sd, by=c('lat','lon'))
}

######################################

for(m in available_models){

    raster_df = get_phenocam_forecast_df(phenocam_forecast, model_name = m)
    
    if(nrow(raster_df)==0){
      next()
    }
    
    filename_base = paste('phenocam',m,issue_date,sep='_')
    #################
    # Prediction titles and filename
    figure_title_prediction = paste0('Phenocam Forecasts - Model: ',m)
    figure_subtitle_prediction = paste0('Issued ',issue_date_abbr)
    legend_title_prediction = paste0('Date of phenocam green up')
    static_filename_prediction = paste0(filename_base,'_prediction.png')

    #################
    # Uncertainty titles and filename
    figure_title_uncertainty = paste0('Phenocam Forecasts - Model: ',m)
    figure_subtitle_uncertainty = paste0('Uncertainty for date of phenocam green up. Issued ',issue_date_abbr)
    legend_title_uncertainty = paste0('95% CI for green up in days')
    static_filename_uncertainty = paste0(filename_base,'_uncertainty.png')

    ################
    # stand alone static image prediction
    static_image_prediction= static_image_base_plot +
      geom_raster(data = raster_df, aes(x=lat, y=lon, fill=doy_prediction), alpha=1) +
      geom_polygon(data = basemap, aes(x=long, y = lat, group = group), fill=NA, color='grey20', size=0.3) + 
      scale_fill_gradientn(colors=prediction_color_scheme, labels = doy_to_date, limits=c(1,365), 
                           breaks=legend_label_breaks) + 
      theme(legend.key.width = unit(2.5, 'cm')) +
      labs(title = figure_title_prediction, 
           subtitle = figure_subtitle_prediction,
           fill = legend_title_prediction)
    
    ggsave(static_image_prediction,filename=paste0(issue_date_forecast_folder,static_filename_prediction),
           height = 12.5, width = 17, units = 'cm')
    
    ##############
    # Convert SD to 95% CI, and max out uncertainty to 30 days.
    raster_df$doy_sd = raster_df$doy_sd*2
    raster_df$doy_sd = with(raster_df , ifelse(doy_sd<30, doy_sd, 30))
    
    # static image for uncertainty
    static_image_uncertainty=static_image_base_plot + 
      geom_raster(data = raster_df, aes(x=lat, y=lon, fill=doy_sd)) +
      geom_polygon(data = basemap, aes(x=long, y = lat, group = group), fill=NA, color='grey20', size=0.3) + 
      scale_fill_distiller(palette='YlGnBu', direction = 1, limits=c(0,30), breaks=uncertainty_legend_breaks,
                           labels = uncertainty_legend_labels) +
      guides(fill = guide_colorbar(title = legend_title_uncertainty,
                                   title.position = 'top',
                                   title.hjust = 0.5)) + 
      theme(legend.key.width = unit(1.0, 'cm')) +
      labs(title = figure_title_uncertainty, 
           subtitle = figure_subtitle_uncertainty,
           fill = legend_title_uncertainty)
    
    ggsave(static_image_uncertainty,filename=paste0(issue_date_forecast_folder,static_filename_uncertainty),
           height = 12.5, width = 17, units = 'cm')
    
    
    # 
    # # Display only the data for interactive map
    # # TODO: need to change CRS
    # r = raster_from_netcdf(phenocam_forecast, phenophase = pheno, species =  spp, variable = 'doy_prediction')
    # raster::crs(r) = crs_used
    # map_image = raster_to_leaflet_image(r, colors=color_scheme, color_domain = c(0,365))
    # 
    # png::writePNG(map_image, target=paste0(issue_date_forecast_folder,map_filename))
    
    # image_metadata = image_metadata %>%
    #   bind_rows(data.frame(species=spp, common_name = common_name, phenophase=pheno, 
    #                        forecast_issue_date=issue_date,img_filename=c(static_filename_prediction, static_filename_uncertainty)))
}

#append_csv(image_metadata, config$phenology_forecast_figure_metadata_file)
