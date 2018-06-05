library(tidyverse)
source('tools/npn_data_tools.R')
source('tools/tools.R')

config = load_config()

current_season_observations = read_csv('/home/shawn/data/phenology/npn_2018/status_intensity_observation_data.csv')
current_season_sites = read_csv('/home/shawn/data/phenology/npn_2018/ancillary_site_data.csv')

# Process to only yes observations preceeded by a no within 30 days
all_observations = current_season_observations %>%
  select(site_id = Site_ID, individual_id = Individual_ID, Phenophase_ID, Observation_Date, status = Phenophase_Status,
         intensity_id = Intensity_Category_ID, intensity = Intensity_Value, Genus, Species) %>%
  mutate(species= tolower(paste(Genus,Species,sep=' ')), 
         year   = lubridate::year(Observation_Date),
         doy    = lubridate::yday(Observation_Date)) %>%
  process_phenology_observations(prior_obs_cutoff = 30)

# add in lat/lon
site_info = current_season_sites %>%
  select(site_id=Site_ID, latitude=Latitude, longitude=Longitude, Site_Type)

all_observations = all_observations %>%
  left_join(site_info, by='site_id')

# Drop group sites
all_observations = all_observations %>%
  filter(Site_Type!='Group')

if(sum(is.na(all_observations$latitude))>0){
  warning('some missing coordinates')
}

# Add in a unique observation ID for every species and phenophase
all_observations = all_observations %>%
  group_by(species, Phenophase_ID) %>%
  mutate(observation_id = 1:n()) %>%
  ungroup()

write_csv(all_observations, config$phenology_current_season_observation_file)
