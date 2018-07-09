library(tidyverse)
source('tools/tools.R')

config=load_config()


# For 2018 hindcasting, using species with at least 10 observations in 2018
# and at least 30 observations prior to 2017 (which was used for model building)

current_season_sample_sizes = read_csv(config$phenology_current_season_observation_file) %>%
  group_by(species, Phenophase_ID) %>%
  tally() %>%
  filter(Phenophase_ID %in% c(371,501)) %>%
  filter(n>=10)

# The species list has info for all species from prior years
available_models = read_csv(config$species_list_file) %>%
  filter(n_observations>=30)

species_for_hindcasting = available_models %>%
  filter(interaction(species, Phenophase_ID) %in% interaction(current_season_sample_sizes$species, current_season_sample_sizes$Phenophase_ID))

species_for_hindcasting$current_forecast_version=4

write_csv(species_for_hindcasting, paste0(config$data_folder,'species_for_hindcasting.csv'))
