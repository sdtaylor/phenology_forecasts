library(tidyverse)
library(raster)
library(viridis)
library(ncdf4)
library(lubridate)
#library(leaflet)
source('map_utils.R')

config = load_config()

##################################################
# TODO: put this in a file if a bunch of this gets added
all_phenophase_info = data_frame(Phenophase_ID = c(371,501),
                                 noun = c('leaf','flower'),
                                 noun_plural = c('leaves','flowers'),
                                 verb = c('leaf out','flowering'))

species_info = read_csv(config$species_list_file)

####################################################

today = as.character(Sys.Date())
# Like Jan. 3, 2018
today_abr = strftime(Sys.Date(), '%b %d, %Y')
current_season=current_growing_season()

args=commandArgs(trailingOnly = TRUE)
#phenology_forecast_filename = args[1]
phenology_forecast_filename = '/home/shawn/data/phenology_forecasting/phenology_forecasts/phenology_forecast_2018-01-05.nc'
phenology_forecast = ncdf4::nc_open(phenology_forecast_filename)

todays_forecast_folder = paste0(config$phenology_forecast_figure_folder,today,'/')
dir.create(todays_forecast_folder)

available_species = phenology_forecast$dim$species$vals
available_phenophases = phenology_forecast$dim$phenophase$vals

image_metadata=data.frame()

basemap = map_data('state')

#color_scheme = c('blue','green1','green4','red','yellow','cyan')
# This one is hopefully somewhat colorblind friendly
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
    figure_subtitle = paste0('Predicted date of ',phenophase_info$verb,' for ',current_season,' - Issued ',today_abr)
    legend_title = paste0('Date of ',tools::toTitleCase(phenophase_info$verb))
    figure_filename = paste(stringr::str_replace(spp,' ','_'),pheno,today,sep='_')
    figure_filename = paste0(figure_filename,'.png')
    
    
    p=ggplot() + 
      #geom_hex(data = species_data, aes(x=lat, y=lon, color=doy_prediction), bins=10)+
      geom_raster(data = raster_df, aes(x=lat, y=lon, fill=doy_prediction)) +
      scale_fill_gradientn(colors=color_scheme, labels = doy_to_date, limits=c(1,365)) + 
      geom_polygon(data = basemap, aes(x=long, y = lat, group = group), fill=NA, color='grey20', size=0.5) + 
      coord_fixed(1.3) +
      theme_bw() + 
      guides(fill = guide_colorbar(title = legend_title,
                                   title.position = 'top',
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
      labs(title = figure_title, 
           subtitle = figure_subtitle)
    
    ggsave(p,filename=paste0(todays_forecast_folder,figure_filename),
           height = 25, width = 34, units = 'cm')
   
    image_metadata = image_metadata %>%
      bind_rows(data.frame(species=spp, common_name = common_name, phenophase=pheno, 
                           forecast_issue_data=today,img_filename=figure_filename))
     
  }
}

append_csv(image_metadata, config$phenology_forecast_figure_metadata_file)


