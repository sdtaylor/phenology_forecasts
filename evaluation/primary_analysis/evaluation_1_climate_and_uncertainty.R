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
hindcasts_primary_method = load_hindcast_data(hindcasts_file = paste0(config$data_folder,'evaluation/hindcast_data_2018.csv'),
                                  observations_file = paste0(config$data_folder,'evaluation/phenology_2018_observations.csv'),
                                  year=2018) %>%
  calculate_point_estimates(hindcast_prediction_levels = c('species','Phenophase_ID','site_id','latitude','longitude','year','observation_id','issue_date'),
                            add_sd=T) 

# And the one to compare with which uses only observations (PRISM) integrated with long term averages
# the group_split %> map_dfr is important here to keep memory usage reasonable. Files are 4-9 GB
hindcasts_lta_method = load_hindcast_data(hindcasts_file = paste0(config$data_folder,'evaluation/hindcast_lta_method_data_2018.csv'),
                                      observations_file = paste0(config$data_folder,'evaluation/phenology_2018_observations.csv'),
                                      year=2018) %>%
  calculate_point_estimates(hindcast_prediction_levels = c('species','Phenophase_ID','site_id','latitude','longitude','year','observation_id','issue_date'),
                            add_sd=T) 

hindcasts_primary_method$method = 'primary'
hindcasts_lta_method$method = 'observed_temp_only'

hindcasts_with_issue_dates = hindcasts_primary_method %>%
  bind_rows(hindcasts_lta_method)

#####################################
#####################################
# combine the hindcast, naive, and long term averages.
# do some fancy pivots to make a tidy data.frame like
# species, phenophase, site_id, obseration_id, ... , doy_observed, method, doy_prediction, doy_prediciton_sd
# acer, 501, 1531, 441,                              30,          primary_model, 65, 2   
# acer, 501, 1531, 441,                              30,          lta          , 55, 5
#
# pivot_wider and pivot_longer require tidyr>=1.0.0

long_term_average_data = load_long_term_averages(long_term_average_file = paste0(config$data_folder,'evaluation/long_term_average_model_data_2018.csv'),
                                                 year=2018) %>%
  rename(doy_prediction_sd_lta = doy_sd_lta)

hindcasts_with_issue_dates = hindcasts_with_issue_dates %>%
  pivot_wider(names_from = 'method', values_from = c('doy_prediction','doy_prediction_sd')) %>%
  left_join(long_term_average_data, by=c('species','Phenophase_ID','site_id','year')) %>%
  pivot_longer(cols = contains('doy_prediction'),
               names_to = c('.value','method'),
               names_pattern = '(doy_prediction_sd|doy_prediction)_(primary|observed_temp_only|lta)')

#####################################
####################################

hindcasts_with_issue_dates = hindcasts_with_issue_dates %>%
  mutate(error = doy_prediction - doy_observed)

#####################################
####################################
# Figure X: total RMSE vs lead time or issue date
####################################
#####################################

plot_theme =  theme_bw() + 
              theme(plot.title = element_text(size=18),
                    axis.text = element_text(size=16),
                    axis.title = element_text(size=18),
                    strip.text = element_text(size=28),
                    legend.text = element_text(size=16),
                    legend.key.width = unit(20,'mm'),
                    legend.title = element_blank(),
                    legend.background = element_rect(color='black'),
                    legend.position = 'none') 

line_colors = c('#E69F00',"black", "grey60")

rmse_range = c(8,24)
coverage_range = c(0.6, 0.98)

# Issue date plots
issue_date_errors = hindcasts_with_issue_dates %>%
  #filter(species == 'acer rubrum') %>%
  mutate(p = pnorm(doy_observed, doy_prediction, doy_prediction_sd)) %>% # probability of observation given prediction, used for coverage
  group_by(issue_date, year, method) %>%
  summarise(rmse = sqrt(mean(error**2, na.rm = T)),
            mae = mean(abs(error), na.rm = T),
            coverage = mean(p > 0.025 & p < 0.975, na.rm=T),
            n=n(),
            num_na = sum(is.na(error)),
            n_species_phenophase = n_distinct(interaction(species, Phenophase_ID))) %>%
  ungroup()


issue_date_errors$method = factor(issue_date_errors$method, 
                                  levels = c('lta','observed_temp_only','primary'), 
                                  labels = c('Long Term Average','Observed Temp. Integration Only','Observed Temp. + Forecasts Integration'))

issue_date_rmse_plot = ggplot(issue_date_errors, aes(x=issue_date, y=rmse, color=method)) + 
  geom_line(size=3) +
  scale_color_manual(values = line_colors) + 
  scale_x_date(breaks = as.Date(c('2017-12-01','2018-01-01', '2018-02-01', '2018-03-01', '2018-04-01', '2018-05-01', '2018-06-01'))) + 
  #scale_y_continuous(limits = c(14,23)) + 
  labs(y='RMSE', title = 'A. RMSE with respect to issue date') +
  plot_theme +
  theme(axis.title.x = element_blank(),
        axis.text.x = element_blank(),
        axis.ticks.x = element_blank(),
        legend.position = 'none')

issue_date_coverage_plot = ggplot(issue_date_errors, aes(x=issue_date, y=coverage, color=method)) + 
  geom_line(size=3) +
  geom_segment(y=0.95, yend=0.95, x=-120, xend=0, color='black', linetype='dashed', size=2) +
  geom_hline(yintercept = 0.95, size=2, linetype='dotted') + 
  scale_color_manual(values = line_colors) + 
  scale_x_date(breaks = as.Date(c('2017-12-01','2018-01-01', '2018-02-01', '2018-03-01', '2018-04-01', '2018-05-01', '2018-06-01')),
               labels = function(x){format(x,'%b. %d')}) + 
  #scale_y_continuous(limits = coverage_range) + 
  labs(y = 'Coverage', x= 'Issue Date', title = 'B. Coverage with respect to issue date') +
  plot_theme 

###############################################


issue_date_rmse_plot + issue_date_mae_plot +  issue_date_coverage_plot + plot_layout(ncol=1)








