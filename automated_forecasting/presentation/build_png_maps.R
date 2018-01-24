library(tidyverse)
library(raster)
library(viridis)
library(ncdf4)
library(lubridate)
#library(leaflet)
source('automated_forecasting/presentation/map_utils.R')

config = load_config()

current_season=current_growing_season()

##################################################
# TODO: put this in a file if a bunch of this gets added
all_phenophase_info = data_frame(Phenophase_ID = c(371,501),
                                 noun = c('leaf','flower'),
                                 noun_plural = c('leaves','flowers'),
                                 verb = c('leaf out','flowering'))

species_info = read_csv(config$species_list_file)

#########################################################################
# Take doy of the current season and return Mar. 1, Jan. 30, etc.
doy_to_date = function(x){
  dates = as.Date(paste(current_season, x,sep='-'), '%Y-%j')
  abbr  = strftime(dates, '%b %d')
  return(abbr)
}
####################################################



args=commandArgs(trailingOnly = TRUE)
#phenology_forecast_filename = args[1]
phenology_forecast_filename = '/home/shawn/data/phenology_forecasting/phenology_forecasts/phenology_forecast_2018-01-23.nc'
phenology_forecast = ncdf4::nc_open(phenology_forecast_filename)

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

#color_scheme = c('blue','green1','green4','red','yellow','cyan')
# This one is hopefully somewhat colorblind friendly. RGB-Hex is the same as the names
# from: https://web.njit.edu/~kevin/rgb.txt.html
#color_scheme = c('87CEEB','9AFF9A','548B54','FF6347','FFFF00','0000FF')
color_scheme = c('skyblue','palegreen1','palegreen4','tomato','yellow','blue')

for(spp in available_species){
  for(pheno in available_phenophases){
    common_name = species_info %>%
      filter(species == spp, Phenophase_ID==pheno) %>%
      pull(common_name)
    
    raster_df = get_forecast_df(phenology_forecast, phenophase = pheno, species =  spp)
    
    if(nrow(raster_df)==0){
      next()
    }
    
    phenophase_info = all_phenophase_info %>%
      filter(Phenophase_ID==pheno)
    
    figure_title = paste0('Phenology Forecasts - ',common_name,' (',spp,') ',phenophase_info$noun_plural)
    figure_subtitle = paste0('Predicted date of ',phenophase_info$verb,' for ',current_season,' - Issued ',issue_date_abbr)
    legend_title = paste0('Date of ',tools::toTitleCase(phenophase_info$verb))
    filename_base = paste(stringr::str_replace(spp,' ','_'),pheno,issue_date,sep='_')
    static_filename = paste0(filename_base,'.png')
    map_filename = paste0(filename_base,'_map.png')
    
    # stand alone image
    static_image=ggplot() + 
      #geom_hex(data = species_data, aes(x=lat, y=lon, color=doy_prediction), bins=10)+
      geom_raster(data = raster_df, aes(x=lat, y=lon, fill=doy_prediction)) +
      scale_fill_gradientn(colors=color_scheme, labels = doy_to_date, limits=c(1,365)) + 
      geom_polygon(data = basemap, aes(x=long, y = lat, group = group), fill=NA, color='grey20', size=0.3) + 
      coord_fixed(1.3) +
      theme_bw() + 
      guides(fill = guide_colorbar(title = legend_title,
                                   title.position = 'top',
                                   title.hjust = 0.5)) + 
      theme(legend.position = 'bottom',
            legend.key.width = unit(2.5, 'cm'),
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
            panel.border = element_blank())+
      labs(title = figure_title, 
           subtitle = figure_subtitle)
    
    ggsave(static_image,filename=paste0(issue_date_forecast_folder,static_filename),
           height = 12.5, width = 17, units = 'cm')
    
    # Display only the data for interactive map
    # TODO: need to change CRS
    r = raster_from_netcdf(phenology_forecast, phenophase = pheno, species =  spp, variable = 'doy_prediction')
    raster::crs(r) = crs_used
    map_image = raster_to_leaflet_image(r, colors=color_scheme, color_domain = c(0,365))

    png::writePNG(map_image, target=paste0(issue_date_forecast_folder,map_filename))
    
    image_metadata = image_metadata %>%
      bind_rows(data.frame(species=spp, common_name = common_name, phenophase=pheno, 
                           forecast_issue_data=issue_date,img_filename=static_filename))
    
     
  }
}

append_csv(image_metadata, config$phenology_forecast_figure_metadata_file)


