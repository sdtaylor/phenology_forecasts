library(tidyverse)
source('tools/tools.R')

config = load_config()
########################################
# Hindcast specific functions located here
source('evaluation/data_prep/load_hindcast_data.R')

hindcasts_big_format = load_hindcast_data(hindcasts_file = paste0(config$data_folder,'evaluation/hindcast_data_2018.csv'),
                                          observations_file = paste0(config$data_folder,'evaluation/phenology_2018_observations.csv'),
                               year=2018)

hindcasts = hindcasts_big_format %>%
  calculate_point_estimates() %>%
  calculate_lead_time(hindcast_prediction_levels = c('species','Phenophase_ID','site_id','year','observation_id'))

####################################
# Only keep observations with at least 90 days of hindcasts and discard any which are greater
# than 90 days. This normalizes all predictions to the same lead time, and makes it so
# all lead times have the same sample size. 
obs_to_keep = hindcasts %>%
  group_by(species, Phenophase_ID, observation_id) %>%
  summarize(has_adequate_lead_time = min(lead_time) <= -90) %>%
  ungroup() 
hindcasts = hindcasts %>%
  left_join(obs_to_keep, by=c('species','Phenophase_ID','observation_id')) %>%
  filter(has_adequate_lead_time) %>%
  select(-has_adequate_lead_time) %>%
  filter(lead_time >= -90, lead_time <=0)


#####################################
naive_data = load_naive_forecasts(naive_forecast_file = paste0(config$data_folder,'evaluation/naive_model_data_2018.csv'),
                                  year=2018) %>%
  select(-doy_sd_naive)

hindcasts = hindcasts %>%
  left_join(naive_data, by=c('species','Phenophase_ID','site_id')) %>%
  rename(primary_model = doy_prediction,
         naive_model = doy_prediction_naive) %>%
  gather(model_type, doy_prediction, primary_model, naive_model)


####################################

hindcasts = hindcasts %>%
  mutate(error = doy_prediction - doy_observed)

####################################
lead_time_errors = hindcasts %>%
  group_by(lead_time, model_type) %>%
  summarise(rmse = sqrt(mean(error**2)),
            mae = mean(abs(error)),
            n=n()) %>%
  ungroup()
ggplot(lead_time_errors, aes(x=lead_time, y=rmse, color=model_type)) + 
  geom_line()

#####################################
# The error model
#####################################
library(gbm)
library(randomForest)
library(pdp)

hindcasts$Phenophase_ID = as.factor(hindcasts$Phenophase_ID)
hindcasts$species = as.factor(hindcasts$species)

error_model = randomForest(error ~  Phenophase_ID + species + latitude + longitude + lead_time, 
                  n.trees = 500,
                  data=hindcasts)

gbm::relative.influence(error_model)


species_pdp_data = partial(error_model, pred.var = c('longitude','latitude','lead_time'), n.trees=500)

ggplot(filter(species_pdp_data, lead_time==0), aes(x=longitude, y=latitude, fill=yhat)) + 
  geom_raster() +
  scale_fill_viridis(discrete = F) +
  theme(legend.position = 'right')


