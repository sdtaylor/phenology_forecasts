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

hindcasts_big_format = load_hindcast_data(hindcasts_file = paste0(config$data_folder,'evaluation/hindcast_data_2018.csv'),
                                          observations_file = paste0(config$data_folder,'evaluation/phenology_2018_observations.csv'),
                               year=2018) %>%
  group_by(species, Phenophase_ID, observation_id) %>%
  filter(runif(1) < 0.25) %>% # drop most observations for memory sake
  ungroup() %>%
  calculate_lead_time(hindcast_prediction_levels = c('species','Phenophase_ID','site_id','phenology_model','bootstrap','year','climate_member','observation_id'))

# hindcasts_18 = load_hindcast_data(hindcasts_file = paste0(config$data_folder,'evaluation/hindcast_data_2018.csv'),
#                                   observations_file = paste0(config$data_folder,'evaluation/phenology_2018_observations.csv'),
#                                   year=2018)
# 
# hindcasts_19 = load_hindcast_data(hindcasts_file = paste0(config$data_folder,'evaluation/hindcast_data_2019.csv'),
#                                   observations_file = paste0(config$data_folder,'evaluation/phenology_2019_observations.csv'),
#                                   year=2019) %>%
#   calculate_lead_time(hindcast_prediction_levels =c('species','Phenophase_ID','site_id','phenology_model','year','climate_member','observation_id'))
# 
# hindcasts_big_format = hindcasts_19

####################################
# Only keep observations with at least 90 days of hindcasts and discard any which are greater
# than 90 days. This normalizes all predictions to the same lead time, and makes it so
# all lead times have the same sample size. 
obs_to_keep = hindcasts_big_format %>%
  group_by(species, Phenophase_ID, observation_id, year) %>%
  summarize(has_adequate_lead_time = min(lead_time) <= -120) %>%
  ungroup() 
hindcasts_big_format = hindcasts_big_format %>%
  left_join(obs_to_keep, by=c('species','Phenophase_ID','observation_id','year')) %>%
  filter(has_adequate_lead_time) %>%
  select(-has_adequate_lead_time) %>%
  filter(lead_time >= -120, lead_time <=0)

##################################################################
# calculate uncertainty for each component
#####################################

total_uncertainty = hindcasts_big_format %>%
  group_by(species, Phenophase_ID, site_id, year, lead_time, observation_id) %>%
  summarise(total_sd = sd(doy_prediction),
            doy_observed = unique(doy_observed),
            doy_prediction = mean(doy_prediction)) %>%
  ungroup()

# parameter_uncertainty = hindcasts_big_format %>%
#   group_by(species, Phenophase_ID, site_id,observation_id, year, lead_time,    phenology_model, climate_member) %>%
#   summarise(parameter_sd = sd(doy_prediction)) %>%
#   ungroup() %>%
#   group_by(species, Phenophase_ID, site_id,observation_id, year, lead_time) %>%
#   summarise(parameter_sd = mean(parameter_sd)) %>%
#   ungroup()
# 
# model_uncertainty = hindcasts_big_format %>%
#   group_by(species, Phenophase_ID, site_id, observation_id, year, lead_time,    phenology_model, climate_member) %>%
#   summarise(doy_prediction = mean(doy_prediction)) %>%
#   ungroup() %>%
#   group_by(species, Phenophase_ID, site_id, observation_id, year, lead_time,    climate_member) %>%
#   summarise(model_sd = sd(doy_prediction)) %>%
#   ungroup() %>%
#   group_by(species, Phenophase_ID, site_id, observation_id, year, lead_time) %>%
#   summarise(model_sd = mean(model_sd)) %>%
#   ungroup()

model_climate_uncertainty = hindcasts_big_format %>%
  group_by(species, Phenophase_ID, site_id, observation_id, year, lead_time,    phenology_model, climate_member) %>%
  summarise(doy_prediction = mean(doy_prediction)) %>%
  ungroup() %>%
  group_by(species, Phenophase_ID, site_id, observation_id, year, lead_time) %>%
  summarise(model_climate_sd = sd(model_climate_sd)) %>%
  ungroup() 

climate_uncertainty = hindcasts_big_format %>%
  group_by(species, Phenophase_ID, site_id, observation_id,year, lead_time,    climate_member) %>%
  summarise(doy_prediction = mean(doy_prediction)) %>%
  ungroup() %>%
  group_by(species, Phenophase_ID, site_id, observation_id,year, lead_time) %>%
  summarise(climate_sd = sd(doy_prediction)) %>%
  ungroup()

all_uncertainty = total_uncertainty %>%
  #left_join(parameter_uncertainty, by=c('species','Phenophase_ID','site_id','observation_id','year','lead_time')) %>%
  #left_join(model_uncertainty, by=c('species','Phenophase_ID','site_id','observation_id','year','lead_time')) %>%
  left_join(climate_uncertainty, by=c('species','Phenophase_ID','site_id','observation_id','year','lead_time')) %>%
  left_join(model_climate_uncertainty, by=c('species','Phenophase_ID','site_id','observation_id','year','lead_time')) %>%
  gather(uncertainty_source,SD, total_sd, climate_sd, model_climate_sd)

aggregate_uncertainty = all_uncertainty %>%
  group_by(uncertainty_source, lead_time) %>%
  summarise(SD = mean(SD, na.rm = T),
            sum_na = sum(is.na(SD)),
            n=n())

aggregate_uncertainty$uncertainty_source = factor(aggregate_uncertainty$uncertainty_source,
                                                  levels=c('total_sd','model_climate_sd','climate_sd'),
                                                  labels=c('Climate + Model + Parameter','Climate + Model','Climate Only'),
                                                  ordered = T)
####################################################################
# Figure XX: total/parameter/model/climate uncertainty over lead time (ie. the ribbon plot)
#####################################

ggplot(aggregate_uncertainty, aes(x=lead_time, y=0, fill=uncertainty_source)) + 
  geom_ribbon(aes(ymin=-SD*1.96, ymax=SD*1.96), alpha=0.95, size=1.2) +
  scale_fill_manual(values=c('#4b3f72','#119da4','#ffc857','grey10')) +
  #ggthemes::scale_fill_colorblind() + 
  theme_bw() + 
  theme(text=element_text(size=20),
        legend.position = 'bottom') +
  labs(x='Lead Time', y = '95% CI', fill='Uncertainty Source')
  
######################################################################
# Figure XX: forecast coverage for each of the sources of uncertainty
###################################################
forecast_coverage = all_uncertainty %>%
  mutate(p = pnorm(doy_observed, doy_prediction, SD)) %>%
  group_by(lead_time, uncertainty_source) %>%
  summarise(coverage = mean(p > 0.025 & p < 0.975, na.rm=T)) %>%
  ungroup() %>%
  mutate(year=2018) %>%
  mutate(uncertainty_source = factor(uncertainty_source,
                                     levels=c('total_sd','model_climate_sd','climate_sd'),
                                     labels=c('Climate + Model + Parameter','Climate + Model','Climate Only'),
                                     ordered = T))

ggplot(forecast_coverage,aes(x=lead_time, y=coverage, color=uncertainty_source)) + 
  geom_line(size=2) +
  scale_color_manual(values=c('#4b3f72','#119da4','#ffc857','grey10')) +
  #ggthemes::scale_color_colorblind() + 
  scale_y_continuous(breaks=seq(0,1,0.2), limits = c(0,1)) + 
  scale_x_continuous(breaks = seq(-120,0,20), labels = function(d){d*-1}) + 
  geom_hline(yintercept = 0.95, size=1, linetype='dashed') + 
  theme_bw() + 
  theme(text=element_text(size=20),
        legend.position = c(0.4,0.2),
        legend.background = element_rect(color='black'),
        legend.key.width = unit(25,'mm')) +
  labs(x='Lead Time', y = 'Coverage',color='Uncertainty Source')

######################################################################
# Ethan plot, coverage of just total vs climate only, split out by year
##########################################################################
# must save 2019 first
forecast_coverage_2019 = forecast_coverage %>%
  mutate(year=2019)


forecast_coverage_2018 %>%
  bind_rows(forecast_coverage_2019) %>%
  filter(uncertainty_source %in% c('Total','Climate')) %>% 
  ggplot(aes(x=lead_time, y=coverage, color=as.factor(year))) + 
  geom_line(size=4) +
  scale_color_manual(values=c('#4b3f72','#ffc857','#119da4','grey10')) +
  geom_hline(yintercept = 0.95, size=1, linetype='dashed') + 
  ylim(0,1) + 
  facet_wrap(~uncertainty_source, ncol=2) + 
  theme_bw() + 
  theme(text=element_text(size=20),
        legend.position = 'bottom') 
