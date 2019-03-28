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
  # Drop any observations where the phenophase was observed
  # but an intensity wasn't entered. Potentially a lot of false positives.
  #filter(!(status==1 & intensity=='-9999')) %>%
  process_phenology_observations(prior_obs_cutoff = 30)

# add in lat/lon
site_info = current_season_sites %>%
  select(site_id=Site_ID, latitude=Latitude, longitude=Longitude, Site_Type)

all_observations = all_observations %>%
  left_join(site_info, by='site_id')

# Drop these group sites where is a lot of disagreement
# among observers
all_observations = all_observations %>%
  filter(!site_id %in% c(21468, 21470, 21471))

if(sum(is.na(all_observations$latitude))>0){
  warning('some missing coordinates')
}

# Add in a unique observation ID for every species and phenophase
all_observations = all_observations %>%
  group_by(species, Phenophase_ID) %>%
  mutate(observation_id = 1:n()) %>%
  ungroup()

write_csv(all_observations, 'analysis/current_season_with_custom_summaries.csv')
