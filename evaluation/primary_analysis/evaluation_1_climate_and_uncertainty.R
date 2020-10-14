library(tidyverse) 
library(viridis)
library(patchwork)
source('tools/tools.R')

config = load_config()
########################################
# This script produces the following
# Figure 2: rmse/coverage aggregated for all observations over all 2018 issue dates
# Figure 3: rmse/coverage for 4 spp. for 2018 issue dates
# Figure S2: point forecasts from the 3 different methods plotted along with dotted line observations

#####################################
#####################################
# Setup the hindcast data for evaluation
########################################

##################################################################
# calculate point predictions (ie. the ensemble average) for each component. These are big dataframes, so the heavy
# lifting is done with data.table commands before switching to tidyverse.
#####################################
calculate_point_predictions = function(hindcast_data_table){
    hindcast_data_table[,list(doy_prediction_sd = sd(doy_prediction, na.rm=T),
                              doy_prediction = mean(doy_prediction, na.rm=T),
                              n=.N,
                              num_na = sum(is.na(doy_prediction)),
                              num_999 = sum(doy_prediction==999, na.rm=T)), 
                          by=list(species, Phenophase_ID, site_id, issue_date)] %>%
    as_tibble()
}
#####################################
#####################################
# Setup the hindcast data for evaluation
########################################

# Load the two main hindcasts. The original ones produced by integrating observation data (PRISM) and
# weather forecasts (CFSv2).
hindcasts_primary_method = data.table::fread(paste0(config$data_folder,'evaluation/hindcast_data_2018.csv')) %>%
  calculate_point_predictions()

# And the one to compare with which uses only observations (PRISM) integrated with long term averages
# the group_split %> map_dfr is important here to keep memory usage reasonable. Files are 4-9 GB
hindcasts_lta_method = data.table::fread(paste0(config$data_folder,'evaluation/hindcast_lta_method_data_2018.csv')) %>%
  calculate_point_predictions()

hindcasts_climatology_method = data.table::fread(paste0(config$data_folder,'evaluation/hindcast_climatology_method_data_2018.csv'))
# ~300 predictions from the Linear model are NA due to weird temperature years
hindcasts_climatology_method = hindcasts_climatology_method[!is.na(doy_prediction)]
hindcasts_climatology_method = calculate_point_predictions(hindcasts_climatology_method)

# Climatology isn't updated with every issue date, so needs to be copied to each one manually
hindcasts_climatology_method = map_dfr(unique(hindcasts_primary_method$issue_date), function(x){mutate(hindcasts_climatology_method, issue_date=x)})

hindcasts_primary_method$method = 'primary'
hindcasts_lta_method$method = 'observed_temp_only'  
hindcasts_climatology_method$method = 'climatology'

all_hindcasts = hindcasts_primary_method %>%
  bind_rows(hindcasts_lta_method) %>%
  bind_rows(hindcasts_climatology_method) %>%
  mutate(issue_date = lubridate::ymd(issue_date))

# remove any instances of NA or 999 predictions, where if any prediction within the 
# full climate/phenology ensemble is NA than drop the whole thing.
# This is ~1% of hindcasts. I theorize it happens cause a species model gets applied well
# outside it's range (or the range of the training data).
all_hindcasts = all_hindcasts %>%
  group_by(species, Phenophase_ID, site_id) %>%
  filter(num_na==0 & num_999 ==0) %>% # all doy_prediction within each grouping must be non-na, otherwise the whole grouping is dropped
  ungroup() 

# Also drop fall color as there is just not that many of them
all_hindcasts = all_hindcasts %>%
  filter(Phenophase_ID!=498)

# Some of the less observed species (~9) were not caluclated with the climatology methods
all_hindcasts = all_hindcasts %>%
  group_by(species, Phenophase_ID, site_id) %>%
  filter(n_distinct(method)==3) %>% 
  ungroup() 

x = all_hindcasts %>%
  group_by(species, Phenophase_ID) %>%
  summarise(n_methods = n_distinct(method),
            methods = paste(unique(method), collapse = ' '))

#####################################
####################################
# Join with observations

observation_data = read_csv(paste0(config$data_folder,'evaluation/phenology_2018_observations.csv')) %>%
  select(site_id, observation_id, Phenophase_ID, species, latitude, longitude, year, doy_observed = doy)

all_hindcasts = all_hindcasts %>%
  inner_join(observation_data, by=c('species','Phenophase_ID','site_id'))

all_hindcasts = all_hindcasts %>%
  mutate(error = doy_prediction - doy_observed)

######################################
most_abundant_spp = all_hindcasts %>%
  select(species, Phenophase_ID, observation_id, site_id, latitude, longitude) %>%
  distinct() %>%
  count(species) %>%
  arrange(-n) %>%
  head(4)

doy_to_date = function(doy){
  as.Date(paste0('2018-',doy), format = '%Y-%j')
}
doy_to_date_str = function(doy){
  format(doy_to_date(doy), '%b %d')
}
assing_nice_method_names = function(df){
  df$method = factor(df$method, 
                    levels = c('climatology','observed_temp_only','primary'), 
                    labels = c('Climatology Only','Observed Temp. + Climatology','Observed Temp. + Forecasts Assimilation'))
  return(df)
}

#####################################
####################################
# Figure 2: total RMSE & coverage vs issue date
####################################
#####################################

plot_theme =  theme_bw() + 
              theme(plot.title = element_text(size=26),
                    axis.text = element_text(size=18, color='black'),
                    axis.title = element_text(size=22),
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
issue_date_errors = all_hindcasts %>%
  mutate(p = pnorm(doy_observed, doy_prediction, doy_prediction_sd)) %>% # probability of observation given prediction, used for coverage
  group_by(issue_date, year, method) %>%
  summarise(rmse = sqrt(mean(error**2, na.rm = T)),
            mae = mean(abs(error), na.rm = T),
            coverage = mean(p > 0.025 & p < 0.975, na.rm=T),
            n=n(),
            num_na = sum(is.na(error)),
            n_species_phenophase = n_distinct(interaction(species, Phenophase_ID))) %>%
  ungroup() %>%
  assing_nice_method_names()

issue_date_rmse_plot = ggplot(issue_date_errors, aes(x=issue_date, y=rmse, color=method)) + 
  geom_line(size=3) +
  scale_color_manual(values = line_colors) + 
  scale_x_date(breaks = as.Date(c('2017-12-01','2018-01-01', '2018-02-01', '2018-03-01', '2018-04-01', '2018-05-01', '2018-06-01'))) + 
  labs(y='RMSE', title = 'A. RMSE', x='Issue Date') +
  plot_theme +
  theme(axis.title.x = element_blank(),
        axis.text.x = element_blank(),
        axis.ticks.x = element_blank(),
        legend.position = c(0.65,0.85))

issue_date_coverage_plot = ggplot(issue_date_errors, aes(x=issue_date, y=coverage, color=method)) + 
  geom_line(size=3) +
  geom_segment(y=0.95, yend=0.95, x=-120, xend=0, color='black', linetype='dashed', size=2) +
  geom_hline(yintercept = 0.95, size=2, linetype='dotted') + 
  scale_color_manual(values = line_colors) + 
  scale_x_date(breaks = as.Date(c('2017-12-01','2018-01-01', '2018-02-01', '2018-03-01', '2018-04-01', '2018-05-01', '2018-06-01')),
               labels = function(x){format(x,'%b. %d')}) + 
  scale_y_continuous(limits = coverage_range) + 
  labs(y = 'Coverage', x= 'Issue Date', title = 'B. Coverage') +
  plot_theme 


avg_error_plot = issue_date_rmse_plot +  issue_date_coverage_plot + plot_layout(ncol=1)

ggsave('evaluation1_manuscript/figs/fig2_avg_rmse_coverage.png',avg_error_plot, height = 10, width=10, dpi=150)

##############################################
##############################################
# Figure 4 errors for 4 most abundant taxon
##############################################
##############################################

facet_labels = most_abundant_spp %>%
  mutate(letter = LETTERS[1:4]) %>%
  mutate(facet_label = paste0(letter,'. ', snakecase::to_sentence_case(species))) %>%
  select(species, facet_label)


# Issue date plots
species_level_issue_date_errors = all_hindcasts %>%
  filter(species %in% most_abundant_spp$species) %>%
  mutate(p = pnorm(doy_observed, doy_prediction, doy_prediction_sd)) %>% # probability of observation given prediction, used for coverage
  group_by(issue_date, year, method, species) %>%
  summarise(rmse = sqrt(mean(error**2, na.rm = T)),
            mae = mean(abs(error), na.rm = T),
            coverage = mean(p > 0.025 & p < 0.975, na.rm=T),
            n=n(),
            num_na = sum(is.na(error)),
            n_species_phenophase = n_distinct(interaction(species, Phenophase_ID))) %>%
  ungroup() %>%
  assing_nice_method_names() %>%
  left_join(facet_labels, by='species')

abundant_spp_error_fig= ggplot(species_level_issue_date_errors, aes(x=issue_date, y=rmse, color=method)) + 
  geom_line(size=3) +
  scale_color_manual(values = line_colors) + 
  scale_x_date(breaks = as.Date(c('2017-12-01','2018-01-01', '2018-02-01', '2018-03-01', '2018-04-01', '2018-05-01', '2018-06-01')),
               labels = function(x){format(x,'%b. %d')}) + 
  facet_wrap(~facet_label, scales='free_y') + 
  labs(y='RMSE', title = '', x='Issue Date') +
  plot_theme +
  theme(axis.title = element_text(size=20),
        axis.text.x = element_text(size=14,hjust = 0.55),
        axis.text.y = element_text(size=16),
        strip.text = element_text(size=18, hjust = 0),
        strip.background = element_blank(),
        legend.text = element_text(size=10),
        legend.position = c(0.83,0.385))

ggsave('evaluation1_manuscript/figs/fig3_abund_spp_errors.png',abundant_spp_error_fig, width=35, height = 20, units='cm', dpi=120)


###################################################################
# Figure S2: point forecasts from the 3 different methods plotted along with dotted line observations
###################################################################
spp_to_plot = most_abundant_spp$species

obs_to_plot = c(1,10,20,25)

point_forecast_examples_fig = all_hindcasts %>%
  filter(species %in% spp_to_plot,
         Phenophase_ID == 501,
         observation_id %in% obs_to_plot) %>%
  assing_nice_method_names() %>%
  ggplot(aes(x = issue_date, y=doy_prediction)) +
  geom_line(aes(color=method), size=2) +
  geom_hline(aes(yintercept = doy_observed), linetype='dotted', size=1) + 
  geom_vline(aes(xintercept = doy_to_date(doy_observed)), linetype='dotted', size=1) + 
  scale_x_date(breaks = as.Date(c('2017-12-01','2018-01-01', '2018-02-01', '2018-03-01', '2018-04-01', '2018-05-01', '2018-06-01')),
               labels = function(x){format(x,'%b. %d')}) + 
  scale_color_manual(values = line_colors) + 
  facet_wrap(species ~ observation_id, scales='free', labeller = label_both) +
  theme_bw() +
  theme(legend.position = c(0.8,0.1),
        axis.text = element_text(color='black'),
        axis.text.x = element_text(angle = 45, hjust=1, size=8),
        axis.title = element_text(size=14),
        legend.text = element_text(size=14),
        legend.key.width = unit(20,'mm')) +
  labs(x='Issue Date', y='Day of Year (DOY)')


ggsave('evaluation1_manuscript/figs/figS2_point_forecast_examples.png', height = 30, width=40, dpi=80, units='cm')  
