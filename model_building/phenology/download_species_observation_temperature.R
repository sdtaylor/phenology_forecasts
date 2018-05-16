library(rnpn)
library(docopt)
library(tidyverse)
library(prism)
library(sp)
source('tools/tools.R')

config=load_config()

################################################
# Define CLI usage
'
Usage:
  download_species_observation_temperature.R [options]
Options:
  --update_prism_files  Update the download prism files to today
  --local_site_file=FILE    Path to the local NPN site file

' -> d
args <- docopt(d)
###############################################

args$local_site_file = '~/data/phenology/npn_core/ancillary_site_data.csv'
options(prism.path = config$daily_prism_folder)

if(args$update_prism_files){
  today = as.character(Sys.Date())
  get_prism_dailys(type = 'tmean', minDate = '2006-02-01', maxDate = today, keepZip = FALSE)
}

# Get the sites and years represented in the data
sites_used=c()
years_used=c()
all_species_files = list.files(config$phenology_observations_folder, full.names = TRUE)
for(s in all_species_files){
  this_species_sites = read_csv(s) %>%
    select(site_id) %>%
    distinct() %>% 
    pull(site_id)
  sites_used = c(sites_used, this_species_sites)
  
  this_species_years = read_csv(s) %>%
    select(year) %>%
    distinct() %>% 
    pull(year)
  years_used = c(years_used, this_species_years)
}
sites_used = base::unique(sites_used)
years_used = base::unique(years_used)
years_used = years_used[!is.na(years_used)]

#NPN Site coordinates
site_info = read_csv(args$local_site_file) %>%
  dplyr::select(site_id=Site_ID, latitude=Latitude, longitude=Longitude) %>%
  dplyr::distinct() %>%
  dplyr::filter(site_id %in% sites_used)

# filter to continental US
site_info = site_info %>%
  filter(longitude <= -65, longitude >=-126,
         latitude <= 50, latitude >=24)

sites_spatial = site_info %>%
  SpatialPointsDataFrame(cbind(.$longitude, .$latitude), data=., 
                         proj4string = CRS('+proj=longlat +datum=WGS84 +no_defs +ellps=GRS80 +towgs84=0,0,0'))

#Only load prism data from years which are needed for this dataset
prism_file_info = ls_prism_data(absPath = TRUE) %>%
  mutate(date=stringr::word(files, 5, 5, sep='_'), year=as.numeric(substr(date,1,4))) 

prism_years = base::unique(prism_file_info$year)

if(any(!years_used %in% prism_years)){
  stop('Some years in phenology data not in prism daily data. Maybe prism data with --update_prism_files ? ')
}

# For finding corrupt prism files
# for(i in 1:nrow(prism_file_info)){
#   print(prism_file_info$abs_path[i])
#   raster::raster(prism_file_info$abs_path[i])
# }

prism_stacked = raster::stack(prism_file_info$abs_path, quick=FALSE)

temp_data = as.data.frame(raster::extract(prism_stacked, sites_spatial)) %>%
  bind_cols(site_info) %>%
  process_extracted_prism_data() 

# Put lat/lon in it as well
temp_data = temp_data %>%
  left_join(site_info, by='site_id')

write_csv(temp_data, config$phenology_observations_temperature_file)


