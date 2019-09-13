library(tidyverse) 
library(viridis)
source('tools/tools.R')

config = load_config()
########################################
# This script produces the following
# Figure X: rmse/mae values over lead time for 2018 and 2019
# Figure X: the gbm modelled errors for latitude x year
# Figure X: the species specific errors (mae on x axis, species/phenophase list on y)

#####################################
#####################################
# Setup the hindcast data for evaluation
########################################
# Hindcast specific functions located here
source('evaluation/data_prep/load_hindcast_data.R')

# Load the two main hindcasts. The original ones produced by integrating observation data (PRISM) and
# weather forecasts (CFSv2).
hindcasts_18 = load_hindcast_data(hindcasts_file = paste0(config$data_folder,'evaluation/hindcast_data_2018.csv'),
                                  observations_file = paste0(config$data_folder,'evaluation/phenology_2018_observations.csv'),
                                  year=2018) %>%
  calculate_point_estimates(hindcast_prediction_levels = c('species','Phenophase_ID','site_id','latitude','longitude','year','observation_id','issue_date')) 

hindcasts_18 = hindcasts_18 %>%
  dplyr::group_split(species, Phenophase_ID) %>%
  purrr::map_dfr( .f = function(x){calculate_lead_time(hindcasts = x,hindcast_prediction_levels =  c('species','Phenophase_ID','site_id','year','observation_id'))})

# And the one to compare with which uses only observations (PRISM) integrated with long term averages
# the group_split %> map_dfr is important here to keep memory usage reasonable. Files are 4-9 GB
hindcasts_lta_18 = load_hindcast_data(hindcasts_file = paste0(config$data_folder,'evaluation/hindcast_lta_method_data_2018.csv'),
                                      observations_file = paste0(config$data_folder,'evaluation/phenology_2018_observations.csv'),
                                      year=2018) %>%
  calculate_point_estimates(hindcast_prediction_levels = c('species','Phenophase_ID','site_id','latitude','longitude','year','observation_id','issue_date')) 

hindcasts_lta_18 = hindcasts_lta_18 %>%
  dplyr::group_split(species, Phenophase_ID) %>%
  purrr::map_dfr( .f = function(x){calculate_lead_time(hindcasts = x,hindcast_prediction_levels =  c('species','Phenophase_ID','site_id','year','observation_id'))})


hindcasts_18$method = 'with_forecasts'
hindcasts_lta_18$method = 'observed_temp_only'

hindcasts = hindcasts_18 %>%
  bind_rows(hindcasts_lta_18)

####################################
# Only keep observations with at least 120 days of hindcasts and discard any issue dates
# which are greater # than 120 days. This normalizes all predictions to the same lead time, and makes it so
# all lead times have the same sample size. 
obs_to_keep = hindcasts %>%
  group_by(species, Phenophase_ID, observation_id, year) %>%
  summarize(has_adequate_lead_time = min(lead_time) <= -120) %>%
  ungroup() 
hindcasts = hindcasts %>%
  left_join(obs_to_keep, by=c('species','Phenophase_ID','observation_id','year')) %>%
  filter(has_adequate_lead_time) %>%
  select(-has_adequate_lead_time) %>%
  filter(lead_time >= -120, lead_time <=0) %>%
  #group_by(species, Phenophase_ID, observation_id) %>%
  #filter(n() == 121) %>% # some obs (like 20) flowered/budbursted after May 30 (the last hindcast day) so don't have exactly 120 days of lead time
  #ungroup() %>%
  I()

#####################################
#####################################
# combine the hindcast, naive, and long term averages

# naive_data = load_naive_forecasts(naive_forecast_file = paste0(config$data_folder,'evaluation/naive_model_data_2018.csv'),
#                                   year=2018)

long_term_average_data = load_long_term_averages(long_term_average_file = paste0(config$data_folder,'evaluation/long_term_average_model_data_2018.csv'),
                                                 year=2018)


hindcasts = hindcasts %>%
  select(-issue_date, -issue_doy) %>%
  spread(method, doy_prediction) %>%
  #left_join(select(naive_data, -doy_sd_naive), by=c('species','Phenophase_ID','site_id','year')) %>%
  left_join(select(long_term_average_data, -doy_sd_lta), by=c('species','Phenophase_ID','site_id','year')) %>%
  rename(primary_model = with_forecasts,
         #naive_model = doy_prediction_naive,
         lta_model = doy_prediction_lta) %>%
  gather(model_type, doy_prediction, primary_model, lta_model, observed_temp_only)

#####################################
####################################

hindcasts = hindcasts %>%
  mutate(error = doy_prediction - doy_observed)

#####################################
####################################
# Figure X: total RMSE vs lead time
####################################
#####################################
yearly_lead_time_errors = hindcasts %>%
  group_by(lead_time, year, model_type) %>%
  summarise(rmse = sqrt(mean(error**2)),
            mae = mean(abs(error), na.rm = T),
            n=n(),
            n_species_phenophase = n_distinct(interaction(species, Phenophase_ID))) %>%
  ungroup()

yearly_lead_time_errors$model_type = factor(yearly_lead_time_errors$model_type, 
                                            levels = c('lta_model','observed_temp_only','primary_model'), 
                                            labels = c('Long Term Average','Observed Temp. Only','Observed + Forecasts'))
#yearly_lead_time_errors$year = factor(yearly_lead_time_errors$year, levels = c(2018,2019), labels = c('2018 Observations (n=837)','2019 Observations (n=1586)'))
ggplot(yearly_lead_time_errors, aes(x=lead_time, y=mae, color=model_type)) + 
  geom_line(size=3) +
  #geom_hline(yintercept = 8.7, size=3, color='orange') + 
  scale_color_manual(values=c('#E69F00',"black", "grey60")) + 
  #ggthemes::scale_color_colorblind() + 
  #facet_wrap(~year, ncol=2) +
  scale_x_continuous(breaks=seq(-120,0,20), labels = function(x){x*-1}) + 
  theme_bw() + 
  theme(text = element_text(size=24),
        strip.text = element_text(size=28),
        legend.text = element_text(size=25),
        legend.key.width = unit(20,'mm'),
        legend.title = element_blank(),
        legend.background = element_rect(color='black'),
        legend.position = c(0.75, 0.85)) +
  labs(x = 'Lead Time in Days', y='Mean Absolute Error (MAE)', color='')

  
