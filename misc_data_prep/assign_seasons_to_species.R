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
           avg_doy < 180 ~ 1,
           avg_doy > 180 ~ 180),
         season_end_doy = case_when(
           avg_doy < 180 ~ 180,
           avg_doy > 180 ~ 365)) %>%
  select(-avg_doy)

species_phenophase_seasons = avg_dates %>%
  select(species, Phenophase_ID, season)

species_list = species_list %>%
  left_join(species_phenophase_seasons, by=c('species','Phenophase_ID'))

write_csv(species_list, config$species_list_file)
