library(tidyverse)
source('tools/tools.R')

config=load_config()

forecasted_species = read_csv(config$species_list_file)

forecast_data = read_csv('/home/shawn/data/phenology_forecasting/validation/forecast_data.csv') %>%
  mutate(issue_doy = lubridate::yday(issue_date)) %>%
  select(-latitude, -longitude) 

#forecast_data$phenology_weight=0.25

select_species = c('acer rubrum','betula lenta','maianthemum canadense','populus deltoides',
                   'prunus serotina')

# forecast_data = forecast_data %>%
#   filter(species %in% select_species)

####################
validation_observations = read_csv(config$phenology_current_season_observation_file) %>%
  filter(interaction(species, Phenophase_ID) %in% interaction(forecasted_species$species, forecasted_species$Phenophase_ID)) %>%
  select(-year, -latitude, -longitude) %>%
  rename(doy_observed = doy)

#############################################
# The weighted estimate and SD among phenology models. calculated for each of the 
# 5 climate ensembles
# then get mean(model variance)
# From https://en.wikipedia.org/wiki/Weighted_arithmetic_mean#Weighted_sample_variance
phenology_model_estimates = forecast_data %>%
  group_by(issue_date, issue_doy, climate_ensemble, species, Phenophase_ID, site_id) %>%
  summarize(phenology_mean = sum(prediction*phenology_weight), 
            phenology_sd = sqrt(sum(phenology_weight*((prediction-phenology_mean)^2))),
            n=n()) %>%
  ungroup() 

# The averange variance among the 5 climate ensembles
phenology_variance = phenology_model_estimates %>%
  group_by(issue_date, issue_doy, species, Phenophase_ID, site_id) %>%
  # The average SD among the 5 climate ensembles for each site
  summarize(phenology_sd = mean(phenology_sd), n=n()) %>%
  ungroup() %>%
  # The average SD among all sites
  # group_by(issue_date, issue_doy, species, Phenophase_ID) %>%
  # summarise(phenology_sd = mean(phenology_sd)) %>%
  # ungroup() %>%
  I

# The average climate varariance
climate_variance = phenology_model_estimates %>%
  group_by(issue_date, issue_doy, species, Phenophase_ID, site_id) %>%
  # Given a mean value for each of the 5
  summarise(climate_sd = sd(phenology_mean)) %>%
  ungroup() %>%
  # The average SD among all sites
  # group_by(issue_date, issue_doy, species, Phenophase_ID) %>%
  # summarise(climate_sd = mean(climate_sd)) %>%
  # ungroup() %>%
  I

total_variance = phenology_model_estimates %>%
  group_by(issue_date, issue_doy, species, Phenophase_ID, site_id) %>%
  summarise(doy_prediction = mean(phenology_mean),
            sum_sq = sum((phenology_mean-doy_prediction)**2),
            total_sd = sqrt(mean(phenology_sd^2) + (sum_sq / (n()-1))),
            n=n()) %>%
  ungroup() %>%
  select(-sum_sq, -doy_prediction) 

all_uncertainty = phenology_variance %>%
  left_join(climate_variance, by=c('issue_date','issue_doy','species','Phenophase_ID', 'site_id')) %>%
  left_join(total_variance, by=c('issue_date','issue_doy','species','Phenophase_ID', 'site_id')) %>%
  gather(uncertainty_source, SD, phenology_sd, climate_sd, total_sd)


################################
# fills in a information for every day. 
# ie. if there were forecasts on doy 20 and 25. Then this copies the doy 20 uncertainty
# to doy 21-24.
all_uncertainty = all_uncertainty %>%
  complete(issue_doy=min(issue_doy):(max(issue_doy)+30), nesting(species, Phenophase_ID, site_id, uncertainty_source)) %>%
  arrange(issue_doy) %>%
  group_by(species, Phenophase_ID, site_id, uncertainty_source) %>%
  mutate(SD = zoo::na.locf(SD, na.rm=FALSE)) %>%
  ungroup()

################################
# Add in validation data to only use forecast data up to the actual event happening
all_uncertainty = all_uncertainty %>%
  left_join(validation_observations, by=c('species','site_id','Phenophase_ID'))

all_uncertainty = all_uncertainty %>%
  mutate(lead_time = (issue_doy - doy_observed))

# Only keep observations with at least 90 days of forecasts
obs_to_keep = all_uncertainty %>%
  group_by(species, Phenophase_ID, observation_id) %>%
  summarize(has_adequate_lead_time = min(lead_time) <= -90) %>%
  ungroup() 

all_uncertainty = all_uncertainty %>%
  left_join(obs_to_keep, by=c('species','Phenophase_ID','observation_id')) %>%
  filter(has_adequate_lead_time) %>%
  select(-has_adequate_lead_time) %>%
  filter(lead_time >= -90, lead_time <=0)

##############################################
all_uncertainty$uncertainty_source = factor(all_uncertainty$uncertainty_source, levels=c("total_sd","phenology_sd","climate_sd"),
                                                  labels=c('Total','Model','Climate'), ordered = TRUE)


aggregate_uncertainty = all_uncertainty %>%
  group_by(uncertainty_source, lead_time) %>%
  summarise(SD = mean(SD, na.rm = T),
            n=n()) %>%
  ungroup()

phenophase_uncertainty = all_uncertainty %>%
  group_by(uncertainty_source, lead_time, Phenophase_ID) %>%
  summarise(SD = mean(SD, na.rm = T),
            n=n()) %>%
  ungroup()
phenophase_uncertainty$Phenophase_ID = factor(phenophase_uncertainty$Phenophase_ID, levels=c(371,501), labels=c('Budburst','Open Flowers'))


species_uncertainty = all_uncertainty %>%
  group_by(uncertainty_source, lead_time, species, Phenophase_ID) %>%
  summarise(SD = mean(SD),
            n=n()) %>%
  ungroup()

###############################################


aggregate_uncertainty_plot = ggplot(aggregate_uncertainty, mapping=aes(x=lead_time, y=0, fill=uncertainty_source)) +
  #geom_crossbar(aes(ymin=-SD*1.96, ymax=SD*1.96, alpha=uncertainty_source), fatten = 0.2) +
  geom_ribbon(aes(ymin=-SD*1.96, ymax=SD*1.96, alpha=uncertainty_source), color='black', size=1.2) + 
  scale_fill_manual(values=c('grey60','#E69F00','#0072B2')) + 
  scale_alpha_manual(values=c(1,1,0.8)) +
  scale_x_continuous(labels = function(x){x*-1}) + 
  labs(y='95% CI in days',x='Lead time in days', fill='', alpha='') +
  theme_bw() +
  theme(legend.position = c(0.6,0.04),
       legend.direction = 'horizontal',
       legend.text = element_text(size=40),
       legend.key.width = unit(4,'cm'),
       legend.key.height = unit(1,'cm'),
       axis.title = element_text(size=48),
       axis.text = element_text(size=40),
       panel.grid = element_line(size=1.5),
       panel.border = element_rect(size=1.8)) 

ggsave('analysis/aggregate_forecast_uncertainty.png', plot = aggregate_uncertainty_plot, height = 40, width = 45, units = 'cm')

#####
aggregate_uncertainty_plot = 5
ggplot(phenophase_uncertainty, mapping=aes(x=lead_time, y=0, fill=uncertainty_source)) +
  #geom_crossbar(aes(ymin=-SD*1.96, ymax=SD*1.96, alpha=uncertainty_source), fatten = 0.2) +
  geom_ribbon(aes(ymin=-SD*1.96, ymax=SD*1.96, alpha=uncertainty_source)) + 
  scale_fill_manual(values=c('grey60','#E69F00','#0072B2')) + 
  scale_alpha_manual(values=c(1,0.9,0.5)) +
  scale_x_continuous(labels = function(x){x*-1}) + 
  facet_wrap(~Phenophase_ID, ncol=1) + 
  labs(y='95% CI in days',x='Lead time in days', fill='', alpha='') +
  theme_bw() +
  theme(legend.position = c(0.6,0.04),
        legend.direction = 'horizontal',
        legend.text = element_text(size=40),
        legend.key.width = unit(4,'cm'),
        legend.key.height = unit(1,'cm'),
        axis.title = element_text(size=48),
        axis.text = element_text(size=40),
        panel.grid = element_line(size=1.5),
        panel.border = element_rect(size=1.8)) 

ggsave('analysis/aggregate_forecast_uncertainty.png', plot = aggregate_uncertainty_plot, height = 37, width = 45, units = 'cm')

#####
aggregate_uncertainty_plot = ggplot(species_uncertainty, mapping=aes(x=lead_time, y=0, fill=uncertainty_source)) +
  #geom_crossbar(aes(ymin=-SD*1.96, ymax=SD*1.96, alpha=uncertainty_source), fatten = 0.2) +
  geom_ribbon(aes(ymin=-SD*1.96, ymax=SD*1.96, alpha=uncertainty_source), color='black', size=0.8) + 
  scale_fill_manual(values=c('grey60','#E69F00','#0072B2')) + 
  scale_alpha_manual(values=c(1,1,0.8)) +
  scale_x_continuous(labels = function(x){x*-1}) + 
  facet_wrap(species~Phenophase_ID) + 
  labs(y='95% CI in days',x='Lead time in days', fill='', alpha='') +
  theme_bw() +
  theme(legend.position = c(0.6,0.04),
        legend.direction = 'horizontal',
        legend.text = element_text(size=40),
        legend.key.width = unit(4,'cm'),
        legend.key.height = unit(1,'cm'),
        axis.title = element_text(size=48),
        axis.text = element_text(size=40),
        strip.text = element_text(size=40),
        panel.grid = element_line(size=1.5),
        panel.border = element_rect(size=1.8)) 

ggsave('analysis/species_forecast_uncertainty.png', plot = aggregate_uncertainty_plot, height = 80, width = 95, units = 'cm')

