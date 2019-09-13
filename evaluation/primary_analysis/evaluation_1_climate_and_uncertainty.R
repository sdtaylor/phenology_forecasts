library(tidyverse) 
library(viridis)
library(patchwork)
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
  calculate_point_estimates(hindcast_prediction_levels = c('species','Phenophase_ID','site_id','latitude','longitude','year','observation_id','issue_date'),
                            add_sd=T) 

hindcasts_18 = hindcasts_18 %>%
  dplyr::group_split(species, Phenophase_ID) %>%
  purrr::map_dfr( .f = function(x){calculate_lead_time(hindcasts = x,hindcast_prediction_levels =  c('species','Phenophase_ID','site_id','year','observation_id'))})

# And the one to compare with which uses only observations (PRISM) integrated with long term averages
# the group_split %> map_dfr is important here to keep memory usage reasonable. Files are 4-9 GB
hindcasts_lta_18 = load_hindcast_data(hindcasts_file = paste0(config$data_folder,'evaluation/hindcast_lta_method_data_2018.csv'),
                                      observations_file = paste0(config$data_folder,'evaluation/phenology_2018_observations.csv'),
                                      year=2018) %>%
  calculate_point_estimates(hindcast_prediction_levels = c('species','Phenophase_ID','site_id','latitude','longitude','year','observation_id','issue_date'),
                            add_sd=T) 

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
  group_by(species, Phenophase_ID, observation_id, method) %>%
  filter(n() == 121) %>% # some obs (about 20 total) flowered/budbursted after May 30 (the last hindcast day) so don't have exactly 120 days of lead time
  ungroup() %>%
  I()

#####################################
#####################################
# combine the hindcast, naive, and long term averages

long_term_average_data = load_long_term_averages(long_term_average_file = paste0(config$data_folder,'evaluation/long_term_average_model_data_2018.csv'),
                                                 year=2018)

hindcasts_point_estimates = hindcasts %>%
  select(-issue_date, -issue_doy, -doy_prediction_sd) %>%
  spread(method, doy_prediction) %>%
  left_join(select(long_term_average_data, -doy_sd_lta), by=c('species','Phenophase_ID','site_id','year')) %>%
  rename(primary_model = with_forecasts,
         lta_model = doy_prediction_lta) %>%
  gather(model_type, prediction_value, primary_model, lta_model, observed_temp_only) %>%
  mutate(prediction_type = 'doy_prediction')

hindcasts_uncertainty = hindcasts %>%
  select(-issue_date, -issue_doy, -doy_prediction) %>%
  spread(method, doy_prediction_sd) %>%
  left_join(select(long_term_average_data, -doy_prediction_lta), by=c('species','Phenophase_ID','site_id','year')) %>%
  rename(primary_model = with_forecasts,
         lta_model = doy_sd_lta) %>%
  gather(model_type, prediction_value, primary_model, lta_model, observed_temp_only) %>%
  mutate(prediction_type = 'doy_sd')

hindcasts = hindcasts_point_estimates %>%
  bind_rows(hindcasts_uncertainty) %>%
  spread(prediction_type, prediction_value)

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
  mutate(p = pnorm(doy_observed, doy_prediction, doy_sd)) %>% # probability of observation given prediction, used for coverage
  group_by(lead_time, year, model_type) %>%
  summarise(rmse = sqrt(mean(error**2, na.rm = T)),
            mae = mean(abs(error), na.rm = T),
            coverage = mean(p > 0.025 & p < 0.975, na.rm=T),
            n=n(),
            num_na = sum(is.na(error)),
            n_species_phenophase = n_distinct(interaction(species, Phenophase_ID))) %>%
  ungroup()


yearly_lead_time_errors$model_type = factor(yearly_lead_time_errors$model_type, 
                                            levels = c('lta_model','observed_temp_only','primary_model'), 
                                            labels = c('Long Term Average','Observed Temp. Integration Only','Observed Temp. + Forecasts Integration'))

plot_theme =  theme_bw() + 
              theme(text = element_text(size=24),
                    strip.text = element_text(size=28),
                    legend.text = element_text(size=16),
                    legend.key.width = unit(20,'mm'),
                    legend.title = element_blank(),
                    legend.background = element_rect(color='black'),
                    legend.position = 'none') 

line_colors = c('#E69F00',"black", "grey60")

rmse_plot = ggplot(yearly_lead_time_errors, aes(x=lead_time, y=rmse, color=model_type)) + 
  geom_line(size=3) +
  scale_color_manual(values = line_colors) + 
  scale_x_continuous(breaks=seq(-120,0,20), labels = function(x){x*-1}) + 
  labs(y='', title = 'A. RMSE') +
  plot_theme +
  theme(axis.title.x = element_blank(),
        axis.text.x = element_blank(),
        axis.ticks.x = element_blank(),
        legend.position = c(0.7, 0.8))

coverage_plot = ggplot(yearly_lead_time_errors, aes(x=lead_time, y=coverage, color=model_type)) + 
  geom_line(size=3) +
  geom_segment(y=0.95, yend=0.95, x=-120, xend=0, color='black', linetype='dashed', size=2) +
  scale_color_manual(values = line_colors) + 
  scale_x_continuous(breaks=seq(-120,0,20), labels = function(x){x*-1}) + 
  scale_y_continuous(breaks=seq(0,1,0.05), limits = c(0.7, 0.98)) + 
  labs(y = '', x= 'Lead Time', title = 'B. Coverage') +
  plot_theme 


rmse_plot + coverage_plot + plot_layout(ncol = 1)


##########################################
# lets forget about lead times and just compare errors at different issue dates
