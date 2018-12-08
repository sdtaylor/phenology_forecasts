library(tidyverse)
library(raster)
library(viridis)
library(ncdf4)
library(lubridate)
#library(leaflet)
source('automated_forecasting/presentation/map_utils.R')
source('tools/tools.R')

config = load_config()

current_season=current_growing_season()

##################################################
# TODO: put this in a file if a bunch of this gets added
all_phenophase_info = data_frame(Phenophase_ID = c(371,501,498),
                                 noun = c('leaf','flower','fall color'),
                                 noun_plural = c('leaves','flowers','fall colors'),
                                 verb = c('leaf out','flowering','fall coloring'))

species_info = read_csv(config$species_list_file)

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
#phenology_forecast_filename = '/home/shawn/data/phenology_forecasting/phenology_forecasts/phenology_forecast_2018-12-03.nc'
phenology_forecast = ncdf4::nc_open(phenology_forecast_filename)

# Naive model (doy ~ latitude) used here as the average DOY to calculate annomolies.
naive_model_forecasts = ncdf4::nc_open(config$phenology_naive_model_file)

crs_used = ncdf4::ncatt_get(phenology_forecast, varid=0, attname='crs')$value

issue_date = ncdf4::ncatt_get(phenology_forecast, varid = 0, attname='issue_date')$value
# create string like Jan. 3, 2018
issue_date_abbr = strftime(as.Date(issue_date), '%b %d, %Y')

issue_date_forecast_folder = paste0(config$phenology_forecast_figure_folder,issue_date,'/')
dir.create(issue_date_forecast_folder, showWarnings = FALSE)

available_species = phenology_forecast$dim$species$vals
available_phenophases = phenology_forecast$dim$phenophase$vals

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

anomaly_legend_breaks = c(-30,0,30)
anomaly_legend_labels = c('30 Days Early',0,'30 Days Late')
########################################
attribution_text_main="phenology.naturecast.org"
attribution_text_data="
Made with data from:
National Phenology Network (usanpn.org)
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

######################################

for(spp in available_species){
  for(pheno in available_phenophases){
    common_name = species_info %>%
      filter(species == spp, Phenophase_ID==pheno) %>%
      pull(common_name)
    
    # extract forecast for this species/phenophase from the netcdf.
    # returning a data.frame of the expected date + st. dev.
    raster_df = get_forecast_df(phenology_forecast, phenophase = pheno, species =  spp)
  
    if(nrow(raster_df)==0){
      next()
    }
  
    # The average doy
    spp_average_doy = raster_from_netcdf(naive_model_forecasts, phenophase = pheno, species = spp, variable = 'doy_prediction') %>%
      #raster_set_change_crs(current=nc_crs, to=new_crs) %>%
      rasterToPoints() %>%
      data.frame()
    colnames(spp_average_doy) = c('lat','lon','long_term_average')
      
    raster_df = raster_df %>%
      left_join(spp_average_doy, by=c('lat','lon'))
    
    phenophase_info = all_phenophase_info %>%
      filter(Phenophase_ID==pheno)
    
    filename_base = paste(stringr::str_replace(spp,' ','_'),pheno,issue_date,sep='_')
    
    #################
    # Prediction titles and filename
    figure_title_prediction = paste0('Plant Phenology Forecasts - ',common_name,' (',capitilize(spp),') ',phenophase_info$noun_plural)
    figure_subtitle_prediction = paste0('Predicted date of ',phenophase_info$verb,' for ',current_season,' - Issued ',issue_date_abbr)
    legend_title_prediction = paste0('Date of ',tools::toTitleCase(phenophase_info$verb))
    static_filename_prediction = paste0(filename_base,'_prediction.png')

    #################
    # Uncertainty titles and filename
    figure_title_uncertainty = paste0('Plant Phenology Forecasts - ',common_name,' (',capitilize(spp),') ',phenophase_info$noun_plural)
    figure_subtitle_uncertainty = paste0('Uncertainty for date of ',phenophase_info$verb,' for ',current_season,' - Issued ',issue_date_abbr)
    legend_title_uncertainty = paste0('95% CI for ',tools::toTitleCase(phenophase_info$verb),' in days')
    static_filename_uncertainty = paste0(filename_base,'_uncertainty.png')

    #################
    # Annomoly titles and filename
    figure_title_anomaly = paste0('Plant Phenology Forecasts - ',common_name,' (',capitilize(spp),') ',phenophase_info$noun_plural)
    figure_subtitle_anomaly = paste0('Anomaly for date of ',phenophase_info$verb,' for ',current_season,' - Issued ',issue_date_abbr)
    legend_title_anomaly = paste0('Anomaly for ',tools::toTitleCase(phenophase_info$verb))
    static_filename_anomaly = paste0(filename_base,'_anomaly.png')
    
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
    # Convert SD to 95% CI, and max out uncertainty to 30 days
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
    
    ###################
    # calculate annomoly. Negative numbers means it's earlier, positive mean it's later than average
    raster_df$anomoly = with(raster_df, doy_prediction-long_term_average)
    
    # static image for annomoly
    static_image_anomaly=static_image_base_plot + 
      geom_raster(data = raster_df, aes(x=lat, y=lon, fill=anomoly)) +
      geom_polygon(data = basemap, aes(x=long, y = lat, group = group), fill=NA, color='grey20', size=0.3) + 
    #  scale_fill_gradient2(midpoint = 0, low='#D55E00', high = '#56B4E9', limits=c(-30,30),
    #                       breaks = anomaly_legend_breaks, labels = anomaly_legend_labels)+
      scale_fill_distiller(type='div', palette='RdYlBu', direction = 1, limits=c(-30,30), breaks=anomaly_legend_breaks,
                           labels = anomaly_legend_labels) +
     # guides(fill = guide_colorbar(title = legend_title_anomaly,
    #                               title.position = 'top',
    #                               title.hjust = 0.5)) + 
      theme(legend.key.width = unit(1.0, 'cm')) +
      labs(title = figure_title_anomaly, 
           subtitle = figure_subtitle_anomaly,
           fill = legend_title_anomaly)
    
    ggsave(static_image_anomaly,filename=paste0(issue_date_forecast_folder,static_filename_anomaly),
           height = 12.5, width = 17, units = 'cm')
    # 
    # # Display only the data for interactive map
    # # TODO: need to change CRS
    # r = raster_from_netcdf(phenology_forecast, phenophase = pheno, species =  spp, variable = 'doy_prediction')
    # raster::crs(r) = crs_used
    # map_image = raster_to_leaflet_image(r, colors=color_scheme, color_domain = c(0,365))
    # 
    # png::writePNG(map_image, target=paste0(issue_date_forecast_folder,map_filename))
    
    image_metadata = image_metadata %>%
      bind_rows(data.frame(species=spp, common_name = common_name, phenophase=pheno, forecast_season = current_season,
                           issue_date=issue_date,
                           image_filename=c(static_filename_prediction, static_filename_uncertainty, static_filename_anomaly),
                           image_type = c('prediction_image','uncertainty_image','anomaly_image')))
    
    image_metadata = image_metadata %>%
      spread(image_type, image_filename)
  }
}

append_csv(image_metadata, config$phenology_forecast_figure_metadata_file)



# The following was used  to convert the old metadata file to the new one with a column fo reach image type
# kept here for safekeeping during transition of website to django
# x= read_csv(config$phenology_forecast_figure_metadata_file)
# x=separate(x,image_filename, c('drop1','drop2','drop3','drop4','image_type'), sep ="_", remove=FALSE) %>% 
#   mutate(image_type = str_sub(image_type, 1,-5), 
#          image_type = paste0(image_type,'_image')) %>% 
#   select(-drop1,-drop2,-drop3,-drop4) %>%
#   distinct() %>% 
#   spread(image_type, image_filename)
# write_csv(x, config$phenology_forecast_figure_metadata_file)
