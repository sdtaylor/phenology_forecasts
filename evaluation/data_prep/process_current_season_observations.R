library(tidyverse)
source('tools/npn_data_tools.R')
source('tools/tools.R')

config = load_config()

current_season_observations = read_csv(paste0(config$data_folder,'evaluation/phenology_data_2019/individual_phenometrics_data.csv'))
current_season_sites = read_csv(paste0(config$data_folder,'evaluation/phenology_data_2019/ancillary_site_data.csv'))

# Drop any conflicts where multiple observers disagree, or single observers
# mark multiple onsets
current_season_observations = current_season_observations %>%
  filter(!Observed_Status_Conflict_Flag %in% c("MultiObserver-StatusConflict","OneObserver-StatusConflict")) %>%
  filter(Multiple_FirstY==0)

# Keep only observations that had a prior 'no' within 30 days
current_season_observations = current_season_observations %>%
  filter(NumDays_Since_Prior_No >0, NumDays_Since_Prior_No<=30)

# Correct observed date as midpoint between 1st 'no' and  most prior 'no'
current_season_observations$First_Yes_DOY = ceiling(with(current_season_observations, First_Yes_DOY - (NumDays_Since_Prior_No/2)))

# Rename to variables I like
current_season_observations = current_season_observations %>%
  select(site_id = Site_ID, individual_id = Individual_ID, Phenophase_ID, Genus, Species, 
         latitude=Latitude, longitude=Longitude,
         year=First_Yes_Year, doy=First_Yes_DOY) %>%
  mutate(species= tolower(paste(Genus,Species,sep=' '))) 

# Add in a unique observation ID for every species and phenophase
current_season_observations = current_season_observations %>%
  group_by(species, Phenophase_ID) %>%
  mutate(observation_id = 1:n()) %>%
  ungroup()

write_csv(current_season_observations, paste0(config$data_folder,'evaluation/phenology_2019_observations.csv'))

