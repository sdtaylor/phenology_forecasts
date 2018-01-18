library(ggplot2)
library(dplyr)
library(raster)
library(viridis)
library(ncdf4)
library(lubridate)
library(leaflet)
source('map_utils.R')


n = ncdf4::nc_open('/home/shawn/data/phenology_forecasting/phenology_forecasts/phenology_forecast_2018-01-05.nc')


species = 'acer rubrum'
Phenophase_ID = 501
r_df = get_forecast_df(n, phenophase = Phenophase_ID, species = species, downscale_factor=10)

all_phenophase_info = data.frame(Phenophase_ID = c(371,501),
                             noun = c('leaf','flower'),
                             noun_plural = c('leaves','flowers'),
                             verb = c('leaf out','flowering'))

# Make them dates with 95% confidence intervals
current_year = 2018
r_df$prediction_date = as_date(paste(current_year, r_df$doy_prediction,sep='-'), '%Y-%j')
r_df$first_day = with(r_df, prediction_date - days(round(doy_sd*2,0)))
r_df$last_day =  with(r_df, prediction_date + days(round(doy_sd*2,0)))


r_df = r_df[1:10,]

##############################################################
# leaflet stuff
r = raster_from_netcdf(n, Phenophase_ID, species, 'doy_prediction', downscale_factor=10)

# Simpify to whole days
r = raster::calc(r, fun = function(x){round(x,0)})

crs(r) <- CRS('+init=epsg:4269') # Temporary until #15
min_value = min(values(r), na.rm = T)
max_value = max(values(r), na.rm = T)

leaflet_color_scheme = leaflet::colorNumeric(c("#0C2C84", "#41B6C4", "#FFFFCC"), c(min_value, max_value),
                                             na.color = 'transparent')



leaflet() %>% addTiles() %>%
  addRasterImage(r, colors = leaflet_color_scheme, opacity = 0.85) %>%
  addPopups(~lat, ~lon, popup = ~as.character(prediction_date),
            options = popupOptions(closeButton = FALSE), data=r_df) %>%
  addLegend(pal = leaflet_color_scheme,
            values = values(r),
            bins=5,
            labels = doy_to_date(unique(values(r))),
            title='Day of Flowering')

#################################################################


basemap = map_data('state')

# Take doy of the current season and return Mar. 1, Jan. 30, etc.
doy_to_date = function(x){
  dates = as_date(paste(current_year, x,sep='-'), '%Y-%j')
  abbr  = strftime(dates, '%b %d')
  return(abbr)
}

phenophase_info = filter(all_phenophase_info, Phenophase_ID==Phenophase_ID)

map_title = paste('Phenology Forecasts ',species_common_name,' (',species,') ',phenophase)


