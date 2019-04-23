library(tidyverse)
#library(raster)
library(ncdf4)
library(raster)
library(kableExtra)

source('automated_forecasting/presentation/map_utils.R')
source('tools/tools.R')

config = load_config()
################################################################
################################################################
# Table S1, list of species and their phenophases for which forecasts are made

# This goes thru some recent forecast nc files and filters out which ones actually
# end up on the website.
################################################################
################################################################

species_cell_counts_file = paste0(config$data_folder,'evaluation/species_cell_counts.csv')

phenology_forecasts_files = c(paste0(config$data_folder,'phenology_forecasts/2018/phenology_forecast_2018-09-01.nc'),
                              paste0(config$data_folder,'phenology_forecasts/2018/phenology_forecast_2018-11-08.nc'),
                              paste0(config$data_folder,'phenology_forecasts/phenology_forecast_2019-01-01.nc')
                              )


parse_forecasts_for_cell_counts = function(){
  forecast_info = tibble()
  for(f in phenology_forecasts_files){
    phenology_forecast_object = ncdf4::nc_open(f)
    
    issue_date = ncdf4::ncatt_get(phenology_forecast_object, varid = 0, attname='issue_date')$value
    
    available_species = phenology_forecast_object$dim$species$vals
    available_phenophases = phenology_forecast_object$dim$phenophase$vals
    
    for(species in available_species){
      for(phenophase in available_phenophases){
        
        raster_df = get_forecast_df(phenology_forecast_object, phenophase = phenophase, species =  species)
        
        forecast_info = forecast_info %>%
          bind_rows(tibble(species=species, 
                           phenophase=phenophase,
                           num_cells = nrow(raster_df),
                           issue_date = issue_date))
        
      }
    }
  }
  
  return(forecast_info)
}

if(file.exists(species_cell_counts_file)){
  species_cell_counts = read_csv(species_cell_counts_file)
} else {
  species_cell_counts = parse_forecasts_for_cell_counts()
  write_csv(species_cell_counts, species_cell_counts_file)
}

###################################################
# capitilize the first letter of a string. 
capitilize = function(s){
  l = toupper(substr(s, 1,1))
  return(paste0(l,substr(s,2,nchar(s))))
}

add_phenophase_name_col = function(df){
  df %>%
    mutate(phenophase_name = case_when(
      phenophase==371 ~ 'Budburst',
      phenophase==501 ~ 'Flowers',
      phenophase==498 ~ 'Fall Colors',
      phenophase==390 ~ 'Ripe Fruits'
    ))
}
########################################

species_cell_counts = species_cell_counts %>%
  add_phenophase_name_col() %>%
  dplyr::filter(num_cells > 0) %>%
  distinct()

phenophase_totals = species_cell_counts %>%
  group_by(phenophase_name) %>%
  summarise(cell_content = as.character(n())) %>%
  ungroup() %>%
  mutate(species='zTotal') # add a z so it ends up last in the table, will remove it in the supplement doc

species_table = species_cell_counts %>%
  mutate(species = capitilize(species)) %>%
  mutate(cell_content = '$\\checkmark$') %>%
  dplyr::select(species, phenophase_name, cell_content) %>%
  bind_rows(phenophase_totals) %>%
  spread(phenophase_name, cell_content, fill='') 

# add a left side index column
species_table = tibble(index=1:nrow(species_table)) %>%
  bind_cols(species_table)

# copy/paste to supplement.md
kable(species_table, 'markdown')

################################################################
################################################################
# Table S1. species stats in the 2019 eval data
################################################################
################################################################


forecast_data = read_csv(paste0(config$data_folder,'evaluation/forecast_data_2019.csv')) %>%
  dplyr::select(-latitude, -longitude) 
eval_observations =  read_csv(paste0(config$data_folder,'evaluation/phenology_2019_observations.csv')) %>%
  dplyr::select(-latitude, -longitude) %>%
  rename(doy_observed = doy)

# Combine obserations + forecasts for all the different issue dates. 
# drop anything with missing data. which can happen when an observations is outside
# the range for a respective species.
eval_observations = forecast_data %>%
  left_join(eval_observations, by=c('site_id','Phenophase_ID','species')) %>%
  filter(complete.cases(.))

eval_data_table = eval_observations %>%
  rename(phenophase=Phenophase_ID) %>%
  add_phenophase_name_col() %>%
  mutate(species = capitilize(species)) %>%
  group_by(species, phenophase_name) %>%
  summarise(total_obs = n(),
            mean_doy = round(mean(doy_observed),0)) %>%
  ungroup()

# Add Totals row at the bottom.
eval_data_table = eval_data_table %>%
  bind_rows(tibble(species='Total',
                   total_obs = sum(eval_data_table$total_obs),
                   mean_doy = round(mean(eval_observations$doy_observed),1)))

# add a left side index column
eval_data_table = tibble(index=1:nrow(eval_data_table)) %>%
  bind_cols(eval_data_table)

# copy/paste to supplement.md
kable(eval_data_table, 'markdown')  
  
  
  

