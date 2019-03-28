library(tidyverse)
source('tools/tools.R')


#####################
# This script reads in the raw forecasts, naive forecasts, and observations
# and combines them for primary analysis.


config=load_config()

forecasted_species = read_csv('/home/shawn/data/phenology_forecasting/species_for_hindcasting.csv')

species_habit = forecasted_species %>%
  select(species,habit) %>%
  distinct() %>%
  mutate(habit = tools::toTitleCase(habit))

validation_observations = read_csv(config$phenology_current_season_observation_file) %>%
  filter(interaction(species, Phenophase_ID) %in% interaction(forecasted_species$species, forecasted_species$Phenophase_ID)) %>%
  select(-year, -latitude, -longitude) %>%
  rename(doy_observed = doy)

site_info = read_csv(config$phenology_current_season_observation_file) %>%
  select(site_id, longitude, latitude) %>%
  distinct()

forecast_data = read_csv('/home/shawn/data/phenology_forecasting/validation/forecast_data.csv') %>%
  mutate(issue_doy = lubridate::yday(issue_date)) %>%
  mutate(issue_doy = ifelse(issue_date < '2018-01-01', -1* (as.Date('2018-01-01') - issue_date), issue_doy)) %>%
  select(-latitude, -longitude) 

# Drop any site if there are NA values in it's forecast timeseries. 
# Likely an issue with the cropping of the images
forecast_data = forecast_data %>%
  group_by(species, Phenophase_ID, site_id) %>%
  filter(sum(is.na(prediction))==0)

##############################################
# Create a separate Ensemble model forecast
ensemble_model_forecast = forecast_data %>%
  # Mean and variance among the 4 models
  group_by(issue_date,issue_doy, climate_ensemble, species, Phenophase_ID, site_id) %>%
  summarize(prediction_mean = sum(prediction*phenology_weight), 
            phenology_sd = sqrt(sum(phenology_weight*((prediction-prediction_mean)^2))),
            n=n()) %>%
  ungroup() %>%
  # Mean and variance among the 5 climate ensembles
  group_by(Phenophase_ID, issue_date, site_id, species, issue_doy) %>%
  summarise(doy_prediction = mean(prediction_mean),
            sum_sq = sum((prediction_mean-doy_prediction)**2),
            doy_sd = sqrt(mean(phenology_sd^2) + (sum_sq / (n()-1)))) %>%
  ungroup() %>%
  select(-sum_sq) %>%
  mutate(phenology_model='Ensemble') 


# Of the 4 base models, get their mean and SD among the climate ensembles
# base_model_forecasts = forecast_data %>%
#   group_by(Phenophase_ID,species, issue_date, issue_doy, site_id, phenology_model) %>%
#   summarise(doy_prediction = mean(prediction),
#             doy_sd = sd(prediction)) %>%
#   ungroup()


#forecast_data = base_model_forecasts %>%
#   bind_rows(ensemble_model_forecast)
forecast_data = ensemble_model_forecast

################################
# fills in a foreast for every day. 
# ie. if there were forecasts on doy 20 and 25. Then this copies the doy 20 forecast
# to doy 21-24.
forecast_data = forecast_data %>%
  complete(issue_doy=min(issue_doy):(max(issue_doy)+30), nesting(species, Phenophase_ID, site_id, phenology_model)) %>%
  arrange(issue_doy) %>%
  group_by(species, Phenophase_ID, site_id, phenology_model) %>%
  mutate(doy_prediction = zoo::na.locf(doy_prediction, na.rm=FALSE),
         doy_sd = zoo::na.locf(doy_sd, na.rm=FALSE),
         issue_date = zoo::na.locf(issue_date, na.rm=FALSE)) %>%
  ungroup()

################################

naive_forecast_data = read_csv('/home/shawn/data/phenology_forecasting/validation/naive_model_data.csv') %>%
  select(species, Phenophase_ID, site_id, 
         naive_prediction = doy_prediction, naive_prediction_sd = doy_sd)

forecast_data = forecast_data %>%
  left_join(naive_forecast_data, by=c('species','site_id','Phenophase_ID')) %>%
  left_join(validation_observations, by=c('species','site_id','Phenophase_ID'))

forecast_data = forecast_data %>%
mutate(forecast_error = doy_prediction - doy_observed,
       naive_error = naive_prediction - doy_observed)

################################
# This species seems artificially high, potentially due 
# to a lot of observations at relatively few sites
forecast_data = forecast_data %>%
  filter(species != 'amelanchier grandiflora-autumnbrilliance')
################################
