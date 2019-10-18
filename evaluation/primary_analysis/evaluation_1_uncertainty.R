library(tidyverse) 
library(data.table)
library(viridis)
library(patchwork)
library(reticulate)
source('tools/tools.R')

config = load_config()
########################################
# This script produces the following
# Figure X: rmse/mae values over lead time for 2018 and 2019
# Figure X: the gbm modelled errors for latitude x year
# Figure X: the species specific errors (mae on x axis, species/phenophase list on y)


##################################################################
# calculate uncertainty for each component. These are big dataframes, so the heavy
# lifting is done with data.table commands before switching to tidyverse.
#####################################
calculate_uncertainty = function(hindcast_data_table){
  total_uncertainty = hindcast_data_table[,list(total_sd = sd(doy_prediction, na.rm=T),
                                                doy_prediction = mean(doy_prediction, na.rm=T),
                                                n=.N,
                                                num_na = sum(is.na(doy_prediction)),
                                                num_999 = sum(doy_prediction==999, na.rm=T)), 
                                          by=list(species, Phenophase_ID, site_id, issue_date)] %>%
    as_tibble()
  
  
  model_climate_uncertainty = hindcast_data_table[,list(doy_prediction = mean(doy_prediction, na.rm=T)), 
                                                  by=list(species, Phenophase_ID, site_id, issue_date,    phenology_model, climate_member)]
  model_climate_uncertainty = model_climate_uncertainty[,list(model_climate_sd = sd(doy_prediction, na.rm=T)), 
                                                        by=list(species, Phenophase_ID, site_id, issue_date)] %>%
    as_tibble()
  
  climate_uncertainty = hindcast_data_table[,list(doy_prediction = mean(doy_prediction, na.rm=T)), 
                                            by=list(species, Phenophase_ID, site_id, issue_date,  climate_member)]
  climate_uncertainty = climate_uncertainty[,list(climate_sd = sd(doy_prediction, na.rm=T)), 
                                            by=list(species, Phenophase_ID, site_id, issue_date)] %>%
    as_tibble()
  
  
  all_uncertainty = total_uncertainty %>%
    #left_join(parameter_uncertainty, by=c('species','Phenophase_ID','site_id','observation_id','year','issue_date','method')) %>%
    #left_join(model_uncertainty, by=c('species','Phenophase_ID','site_id','observation_id','year','issue_date','method')) %>%
    left_join(climate_uncertainty, by=c('species','Phenophase_ID','site_id','issue_date')) %>%
    left_join(model_climate_uncertainty, by=c('species','Phenophase_ID','site_id','issue_date')) %>%
    gather(uncertainty_source,SD, total_sd, climate_sd, model_climate_sd) %>%
    mutate(issue_date = lubridate::ymd(issue_date))
}
#####################################
#####################################
# Setup the hindcast data for evaluation
########################################
# Hindcast specific functions located here
#source('evaluation/data_prep/load_hindcast_data.R')

# Load the two main hindcasts. The original ones produced by integrating observation data (PRISM) and
# weather forecasts (CFSv2).
hindcasts_primary_method = data.table::fread(paste0(config$data_folder,'evaluation/hindcast_data_2018.csv')) %>%
  calculate_uncertainty()
                                            
# And the one to compare with which uses only observations (PRISM) integrated with long term averages
# the group_split %> map_dfr is important here to keep memory usage reasonable. Files are 4-9 GB
hindcasts_lta_method = data.table::fread(paste0(config$data_folder,'evaluation/hindcast_lta_method_data_2018.csv')) %>%
  calculate_uncertainty()

hindcasts_climatology_method = data.table::fread(paste0(config$data_folder,'evaluation/hindcast_climatology_method_data_2018.csv'))
# ~300 predictions from the Linear model are NA due to weird temperature years
hindcasts_climatology_method = hindcasts_climatology_method[!is.na(doy_prediction)]
hindcasts_climatology_method = calculate_uncertainty(hindcasts_climatology_method)

# Climatology isn't updated with every issue date, so needs to be copied to each one manually
hindcasts_climatology_method = map_dfr(unique(hindcasts_primary_method$issue_date), function(x){mutate(hindcasts_climatology_method, issue_date=x)})
                                        
hindcasts_primary_method$method = 'primary'
hindcasts_lta_method$method = 'observed_temp_only'  
hindcasts_climatology_method$method = 'climatology'

all_uncertainty = hindcasts_primary_method %>%
  bind_rows(hindcasts_lta_method) %>%
  bind_rows(hindcasts_climatology_method)

# remove any instances of NA or 999 predictions, where if any prediction within the 
# full climate/phenology ensemble is NA than drop the whole thing.
# This is ~1% of hindcasts. I theorize it happens cause a species model gets applied well
# outside it's range (or the range of the training data).
all_uncertainty = all_uncertainty %>%
  group_by(species, Phenophase_ID, site_id) %>%
  filter(num_na==0 & num_999 ==0) %>% # all doy_prediction within each grouping must be non-na, otherwise the whole grouping is dropped
  ungroup() 

#######################################################3
# Join with observations

observation_data = read_csv(paste0(config$data_folder,'evaluation/phenology_2018_observations.csv')) %>%
  select(site_id, observation_id, Phenophase_ID, species, latitude, longitude, year, doy_observed = doy)

all_uncertainty = all_uncertainty %>%
  inner_join(observation_data, by=c('species','Phenophase_ID','site_id'))

# aggregate_uncertainty = all_uncertainty %>%
#   group_by(uncertainty_source, issue_date) %>%
#   summarise(SD = mean(SD, na.rm = T),
#             sum_na = sum(is.na(SD)),
#             n=n())
# 
# aggregate_uncertainty$uncertainty_source = factor(aggregate_uncertainty$uncertainty_source,
#                                                   levels=c('total_sd','model_climate_sd','climate_sd'),
#                                                   labels=c('Climate + Model + Parameter','Climate + Model','Climate Only'),
#                                                   ordered = T)

######################################################################
# Figure XX: forecast coverage for each of the sources of uncertainty
###################################################
forecast_coverage = all_uncertainty %>%
  mutate(p = pnorm(doy_observed, doy_prediction, SD)) %>%
  group_by(issue_date, uncertainty_source, method) %>%
  summarise(coverage = mean(p > 0.025 & p < 0.975, na.rm=T), n=n()) %>%
  ungroup() %>%
  mutate(year=2018) %>%
  mutate(uncertainty_source = factor(uncertainty_source,
                                     levels=c('total_sd','model_climate_sd','climate_sd'),
                                     labels=c('Climate + Model + Parameter','Climate + Model','Climate Only'),
                                     ordered = T))

forecast_coverage$method = factor(forecast_coverage$method, 
                   levels = c('climatology','observed_temp_only','primary'), 
                   labels = c('A. Climatology Only','B. Observed Temp. + Climatology','C. Observed Temp. + Forecasts Integration'))

ggplot(forecast_coverage,aes(x=issue_date, y=coverage, color=uncertainty_source)) + 
  geom_line(size=2) +
  scale_color_manual(values=c('#4b3f72','#119da4','#ffc857','grey10')) +
  #ggthemes::scale_color_colorblind() + 
  scale_y_continuous(breaks=seq(0,1,0.2), limits = c(0,1)) +
  scale_x_date(breaks = as.Date(c('2017-12-01','2018-01-01', '2018-02-01', '2018-03-01', '2018-04-01', '2018-05-01', '2018-06-01')),
               labels = function(x){format(x,'%b. %d')}) + 
  geom_hline(yintercept = 0.95, size=1, linetype='dashed') + 
  facet_wrap(~method, ncol=1) + 
  theme_bw() + 
  theme(strip.text =element_text(size=18, hjust = 0),
        strip.background = element_blank(),
        legend.position = c(0.8,0.78),
        legend.background = element_rect(color='black'),
        legend.key.width = unit(25,'mm'),
        legend.text = element_text(size=10),
        legend.title = element_text(size=12),
        axis.text = element_text(size=14),
        axis.title = element_text(size=16)) +
  labs(x='Issue Date', y = 'Coverage',color='Uncertainty Source')
