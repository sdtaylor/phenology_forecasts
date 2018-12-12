library(tidyverse)
source('tools/tools.R')

config=load_config()

species_list = read_csv(config$species_list_file)

#########################################
# From past data quickly discern which season a species/phenophase occurs
# This splits them into two chunks from doy 1-180 and 180-365 based on there mean doy

all_obs= data.frame()
for(i in 1:nrow(species_list)){
  spp_data_filename = paste0(config$phenology_observations_folder,species_list$observation_file[i])
  if(file.exists(spp_data_filename)){
    all_obs = all_obs %>%
      bind_rows(read_csv(spp_data_filename))
  }
}

species_phenophase_seasons = all_obs %>%
  group_by(species, Phenophase_ID) %>%
  summarise(avg_doy = mean(doy)) %>%
  ungroup() %>%
  mutate(season_start_doy = case_when(
           avg_doy < 180 ~ -31,
           avg_doy > 180 ~ 180),
         season_end_doy = case_when(
           avg_doy < 180 ~ 180,
           avg_doy > 180 ~ 320)) %>%
  select(-avg_doy)


# Drop  prior end/start dates to update
if(any(c('season_start_doy','season_end_doy') %in% colnames(species_list))){
  species_list = species_list %>%
    select(-season_start_doy, -season_end_doy)
}

species_list = species_list %>%
  left_join(species_phenophase_seasons, by=c('species','Phenophase_ID'))

# NA's are from species with no observations, where I got models from other people. 
# they're generally in spring so set it to that.
species_list$season_start_doy[is.na(species_list$season_start_doy)] = -31
species_list$season_end_doy[is.na(species_list$season_end_doy)] = 180


write_csv(species_list, config$species_list_file)
