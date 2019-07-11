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

hindcasts_18 = load_hindcast_data(hindcasts_file = paste0(config$data_folder,'evaluation/hindcast_data_2018.csv'),
                                  observations_file = paste0(config$data_folder,'evaluation/phenology_2018_observations.csv'),
                                  year=2018) %>%
  calculate_point_estimates(hindcast_prediction_levels = c('species','Phenophase_ID','phenology_model','site_id','latitude','longitude','year','observation_id','issue_date'))

hindcasts_19 = load_hindcast_data(hindcasts_file = paste0(config$data_folder,'evaluation/hindcast_data_2019.csv'),
                                  observations_file = paste0(config$data_folder,'evaluation/phenology_2019_observations.csv'),
                                  year=2019) %>%
  calculate_point_estimates(hindcast_prediction_levels = c('species','Phenophase_ID','phenology_model','site_id','latitude','longitude','year','observation_id','issue_date')) 

hindcasts = hindcasts_18 %>%
  bind_rows(hindcasts_19) %>%
  mutate(error = doy_prediction - doy_observed)

####################################
# Apply the bias correction model using 2018 data only. 
# This will setup the hindcasts data.frame with doy_prediction for both original and corrected hindcasts
source('evaluation/primary_analysis/bias_correction_functions.R')
bias_correction_model = create_error_model(df = filter(hindcasts, year==2018, issue_date=='2018-05-30'),
                                           model_predictors = c('species','species','Phenophase_ID','phenology_model','longitude','latitude'))

hindcasts = hindcasts %>%
  apply_bias_model(error_model = bias_correction_model) %>%
  calculate_point_estimates(hindcast_prediction_levels = c('species','Phenophase_ID','site_id','latitude','longitude','year','observation_id','issue_date','bias_correction')) %>%
  calculate_lead_time(hindcast_prediction_levels =  c('species','Phenophase_ID','site_id','year','observation_id','bias_correction'))

####################################
# Only keep observations with at least 90 days of hindcasts and discard any which are greater
# than 90 days. This normalizes all predictions to the same lead time, and makes it so
# all lead times have the same sample size. 
obs_to_keep = hindcasts %>%
  group_by(species, Phenophase_ID, observation_id, year) %>%
  summarize(has_adequate_lead_time = min(lead_time) <= -120) %>%
  ungroup() 
hindcasts = hindcasts %>%
  left_join(obs_to_keep, by=c('species','Phenophase_ID','observation_id','year')) %>%
  filter(has_adequate_lead_time) %>%
  select(-has_adequate_lead_time) %>%
  filter(lead_time >= -120, lead_time <=0)

# # also only keep species/phenophases with at least 10 validation observations in a year
# obs_to_keep = hindcasts %>%
#   group_by(species, Phenophase_ID, year) %>%
#   summarize(has_10_obs = n_distinct(observation_id) >= 10) %>%
#   ungroup() 
# hindcasts = hindcasts %>%
#   left_join(obs_to_keep, by=c('species','Phenophase_ID','year')) %>%
#   filter(has_10_obs) %>%
#   select(-has_10_obs)

#####################################
#####################################
naive_data = load_naive_forecasts(naive_forecast_file = paste0(config$data_folder,'evaluation/naive_model_data_2018.csv'),
                                  year=2018) %>%
  bind_rows(load_naive_forecasts(naive_forecast_file = paste0(config$data_folder,'evaluation/naive_model_data_2019.csv'),
                                 year=2019)) %>%
  select(-doy_sd_naive)

hindcasts = hindcasts %>%
  left_join(naive_data, by=c('species','Phenophase_ID','site_id','year')) %>%
  rename(primary_model = doy_prediction,
         naive_model = doy_prediction_naive) %>%
  gather(model_type, doy_prediction, primary_model, naive_model)

#####################################
####################################

hindcasts = hindcasts %>%
  mutate(error = doy_prediction - doy_observed)

#####################################
####################################
# Figure 2: total RMSE vs lead time
####################################
#####################################
yearly_lead_time_errors = hindcasts %>%
  group_by(lead_time, model_type, year, bias_correction) %>%
  summarise(rmse = sqrt(mean(error**2)),
            mae = mean(abs(error)),
            n=n(),
            n_species_phenophase = n_distinct(interaction(species, Phenophase_ID))) %>%
  ungroup()

yearly_lead_time_errors$model_type = factor(yearly_lead_time_errors$model_type, levels = c('naive_model','primary_model'), labels = c('Naive','Primary'))
#yearly_lead_time_errors$year = factor(yearly_lead_time_errors$year, levels = c(2018,2019), labels = c('2018 Observations (n=837)','2019 Observations (n=1586)'))
ggplot(filter(yearly_lead_time_errors, bias_correction=='original'), aes(x=lead_time, y=mae, color=model_type)) + 
  geom_line(size=3) +
  scale_color_manual(values=c("black", "grey60")) + 
  facet_wrap(~year, ncol=2) +
  scale_x_continuous(breaks=seq(-120,0,20), labels = function(x){x*-1}) + 
  theme_bw() + 
  theme(text = element_text(size=24),
        strip.text = element_text(size=28),
        legend.text = element_text(size=30),
        legend.key.width = unit(20,'mm'),
        legend.title = element_blank(),
        legend.background = element_rect(color='black'),
        legend.position = c(0.3, 0.8)) +
  labs(x = 'Lead Time in Days', y='Mean Absolute Error (MAE)', color='')

#################################
#################################
# Figure 6: 2019 error only with bias corrected vs non-corrected
yearly_lead_time_errors %>%
  filter(year==2019) %>%
  select(lead_time, bias_correction, mae, model_type) %>%
  spread(model_type, mae) %>%
ggplot(aes(x=lead_time, y=Primary, color=bias_correction)) + 
  geom_line(size=3) +
  geom_line(aes(y=Naive), size=2, linetype='solid', color='black') + 
  scale_color_manual(values=c("black", "grey60")) + 
  scale_x_continuous(breaks=seq(-120,0,20), labels = function(x){x*-1}) + 
  theme_bw() + 
  theme(text = element_text(size=24),
        strip.text = element_text(size=28),
        legend.text = element_text(size=30),
        legend.key.width = unit(20,'mm'),
        legend.title = element_blank(),
        legend.background = element_rect(color='black'),
        legend.position = c(0.3, 0.8)) +
  labs(x = 'Lead Time in Days', y='Mean Absolute Error (MAE)', color='')


# density of errors by year and naive/primary model
ggplot(filter(hindcasts, lead_time==0), aes(x=error, color=model_type)) + 
  geom_density(fill=NA) + 
  geom_vline(xintercept = 0) + 
  facet_wrap(~year, ncol=2) +
  labs(x = 'Error (prediction - observed)')
# In 2018 the naive model underpredicted, thus it was a late year for most phenology.
# in 2019 the naive model is centered right around 0, thus it was a pretty normal year

####################################
# Figure XX: Ethan plot. mae split out by species/phenophase
####################################
abbreviate_species_names = function(s){                                                                                  
  genus_abbr = paste0(toupper(substr(s, 1,1)), '. ')
  specific_epithet = stringr::word(s, 2,2)
  return(paste0(genus_abbr, specific_epithet))
}

species_errors = hindcasts %>%
  filter(bias_correction=='original') %>%
  group_by(species, Phenophase_ID, lead_time, year) %>%
  summarise(me = mean(error),
            sd = sd(error),
            n=n()) %>%
  ungroup() %>%
  filter(lead_time %in% c(-90,0)) %>%
  filter(n>=10)

species_errors$Phenophase_ID = factor(species_errors$Phenophase_ID, levels=c(371,501),labels=c('Leaves','Flowers'))
species_errors$species_label = as.factor(with(species_errors, paste0(abbreviate_species_names(species),' - ', Phenophase_ID)))
# Rank the species by their error
species_errors$species_label = forcats::fct_reorder(species_errors$species_label, -species_errors$me, .fun = min)

# Setup a nudge based on lead time
y_nudge_base = 0.15
species_errors$y_nudge = with(species_errors, ifelse(lead_time==-90, y_nudge_base, y_nudge_base*-1))

ggplot(species_errors ,aes(x=me, y=species_label, color=as.factor(lead_time))) +
  geom_vline(xintercept = 0, size=1, alpha=0.8) +
  geom_point(size=2, position = position_nudge(x=0, y=species_errors$y_nudge)) +
  geom_errorbarh(aes(xmin = me-sd, xmax = me+sd),  position = position_nudge(x=0, y=species_errors$y_nudge),
                 size=0.8, height = 0.3) + 
  # # again for the other lead time so that these points can be nudged up slightly
  # geom_point(data = filter(species_errors, lead_time==-90), size=2, position = position_nudge(x=0, y=y_nudge)) +
  # geom_errorbarh(data = filter(species_errors, lead_time==-90), aes(xmin = me-sd, xmax = me+sd),  position = position_nudge(x=0, y=y_nudge),
  #                size=0.8, height = 0.3) + 
  scale_color_manual(values = c("#0072B2", "#D55E00")) + 
  #xlim(-20,20) + 
  facet_wrap(~year,ncol=2) + 
  theme_bw() +
  theme(axis.text.y = element_text(size=10),
        axis.title = element_text(size=20),
        legend.text = element_text(size=14),
        legend.title = element_text(size=14),
        axis.text.x = element_text(size=14)) + 
  labs(y='Species - Phenophase (evaluation sample size)',x='Mean Error in Days ± 1 S.D.', color='Lead Time\nin Days')

#####################################
#####################################
# The error model to create pdp plots with
# This is based off the non-bias corrected hindcasts only
#####################################
#####################################

#####################################
library(gbm)
library(pdp)

hindcasts$Phenophase_ID = as.factor(hindcasts$Phenophase_ID)
hindcasts$species = as.factor(hindcasts$species)
hindcasts$year = as.factor(hindcasts$year)

full_error_model = gbm(error ~  species + Phenophase_ID  + latitude + longitude + lead_time + year, 
                       n.trees = 2000, interaction.depth = 2, shrinkage = 0.01, n.cores = 4,
                       data=filter(hindcasts, model_type=='primary_model',  bias_correction=='original'))
# 
# full_error_model = create_error_model(df = filter(hindcasts, model_type=='primary_model', bias_correction=='original'),
#                                       model_predictors = c('species','Phenophase_ID','latitude','longitude','lead_time','year'),
#                                       n.trees = 5000, interaction.depth = 5, shrinkage = 0.1)

gbm::gbm.perf(full_error_model, plot.it = T)

#######################################
# Figure 5: Modelled errors with respect to latitude
######################################
pdp::partial(full_error_model, pred.var = c('latitude','year'), n.trees=2000, plot=F) %>%
  ggplot(aes(y=latitude, x=yhat, color=as.factor(year))) + 
  geom_path(size=3) +
  scale_color_manual(values=c("black", "grey60")) + 
  geom_vline(xintercept = 0) + 
  labs(x='Modelled Error (prediction - observed)', y='Latitude',color='',
       title='') +
  theme_bw() + 
  theme(text=element_text(size=20),
        legend.position = c(0.25, 0.8),
        legend.title = element_blank(),
        legend.text = element_text(size=25),
        legend.key.width = unit(20,'mm'),
        legend.background = element_rect(color='black'))

#######################################
# Figure XX: Modelled errors with respect to lead time
######################################
partial(full_error_model, pred.var = c('lead_time','year'), n.trees=2000, plot=F) %>%
  ggplot(aes(y=yhat, x=lead_time, color=as.factor(year))) + 
  geom_path(size=3) +
  scale_color_manual(values=c("black", "grey60")) + 
  geom_vline(xintercept = 0) + 
  labs(y='Modelled Absolute Error (prediction - observed)', x='Lead Time',color='',
       title='') +
  theme_bw() + 
  theme(text=element_text(size=20),
        legend.position = c(0.25, 0.15),
        legend.title = element_blank(),
        legend.text = element_text(size=25),
        legend.key.width = unit(20,'mm'),
        legend.background = element_rect(color='black'))



