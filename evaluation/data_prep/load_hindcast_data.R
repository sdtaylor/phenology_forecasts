library(tidyverse)
source('tools/tools.R')


#####################
# This script reads in the raw forecasts, naive forecasts, and observations
# and combines them for primary analysis.

load_hindcast_data = function(hindcasts_file, observations_file=NULL, year){
  # Returns a dataframe of hindcasts combined with the associated observed values
  # no aggregation is done, so the predictions are from all climate, model, and bootstrap members. 
  # has the following columns
  #    year, issue_date, phenology_model, bootstrap, doy_observed, species, Phenophase_ID, site_id, doy_prediction, observation_id, longitude, latitude
  #
  # hindcasts_file is a csv with the following columns and produced by hindcasting/hindcasting_site_level.py
  #    phenology_model, bootstrap, site_id, doy_prediction, species, Phenophase_ID, issue_date, climate_member
  #
  # validations_file is a csv with the following columns and produced by validation/data_prep/process_current_season_observations.R
  #    site_id,individual_id,Phenophase_ID,Genus,Species,latitude,longitude,year,doy,species,observation_id

  hindcasts = read_csv(hindcasts_file)
  
  # There is just not that much leaf senesence phenophase
  hindcasts = hindcasts %>% 
    filter(Phenophase_ID != 498)
  
  # 
  
  if(!is.null(observations_file)){
    observation_data = read_csv(observations_file) %>%
      select(site_id, observation_id, Phenophase_ID, species, latitude, longitude, year, doy_observed = doy)
    
    hindcasts = hindcasts %>%
      inner_join(observation_data, by=c('species','Phenophase_ID','site_id'))
  } else {
    # This normally comes with the observation data.
    hindcasts$year = year
  }
  # remove any instances of NA or 999 predictions, where if any prediction within the 
  # full climate/phenology ensemble is NA than drop the whole thing.
  # This is ~1% of hindcasts. I theorize it happens cause a species model gets applied well
  # outside it's range (or the range of the training data).
  hindcasts = hindcasts %>%
    group_by(species, Phenophase_ID, issue_date, site_id) %>%
    filter(all(!is.na(doy_prediction)) & all(doy_prediction!=999)) %>% # all doy_prediction within each grouping must be non-na, otherwise the whole grouping is dropped
    ungroup()
  
  
  # sanity check
  if(!unique(hindcasts$year)==year){
    print('specified argument year does not match year in data')
    print(paste('year:',year))
    print(paste('observations_file:',observations_file))
    print(paste('hindcast_file:',hindcasts_file))
    stop()
  }
  return(hindcasts)
}

load_naive_forecasts = function(naive_forecast_file, year){
 naive = read_csv(naive_forecast_file) %>%
   rename(doy_prediction_naive = doy_prediction,
          doy_sd_naive = doy_sd)
 
 if('latitude' %in% colnames(naive)){
   naive = naive %>%
     select(-latitude, -longitude)
 }
 naive$year = year
 return(naive)
}

calculate_point_estimates = function(hindcasts, hindcast_prediction_levels, add_sd=F){
  # Get the absolute mean of predictions. hindcasts should be output from load_hindcast_data()

  if(add_sd){
    point_estimates = hindcasts %>%
      group_by(!!!rlang::syms(hindcast_prediction_levels)) %>%
      summarise(doy_prediction_sd = sd(doy_prediction),
                doy_prediction = mean(doy_prediction),
                doy_observed_mean = mean(doy_observed),
                doy_observed_unique = unique(doy_observed)) %>%
      ungroup()
    
  } else {
    point_estimates = hindcasts %>%
      group_by(!!!rlang::syms(hindcast_prediction_levels)) %>%
      summarise(doy_prediction = mean(doy_prediction),
                doy_observed_mean = mean(doy_observed),
                doy_observed_unique = unique(doy_observed)) %>%
      ungroup()
    
  }
  
  # Sanity check. the mean and unique value of doy observed should be the same
  if(!all(with(point_estimates, doy_observed_mean == doy_observed_unique))){
    mismatched_entries = which(!with(point_estimates, doy_observed_mean == doy_observed_unique))
    stop('mean of doy != unique_doy for the following rows: ',mismatched_entries)
  }
  
  point_estimates$doy_observed = point_estimates$doy_observed_mean
  point_estimates = point_estimates %>%
    select(-doy_observed_mean, -doy_observed_unique)
  
  return(point_estimates)
}

calculate_lead_time = function(hindcasts, hindcast_prediction_levels, fill_in_all_doys=TRUE){
  # expects a data.frame as returned by load_hindcast_data()
  # and adds an issue_doy and lead_time columns
  # 
  # hindcast_levels, use to fill_in_all_doys is a list of columns which indicate
  # a unique level of predictions, it will generally be all colums in the hindcasts data.frame
  # minus c('issue_date','doy_prediction','doy_observed'). The following are examples dependong on how
  # the hindcasts are aggregated.
  #  c('species','Phenophase_ID','site_id','year','observation_id')
  #  c('species','Phenophase_ID','site_id','year','observation_id','phenology_model')
  #  c('species','Phenophase_ID','site_id','year','observation_id','phenology_model','bootstrap','climate_member')
  #
  if(!all(hindcast_prediction_levels %in% colnames(hindcasts))){
    print(paste('hindcast_prediction_levels: ',hindcast_prediction_levels))
    print(paste('data.frame cols: ',colnames()))
    stop('Not all hindcast_levles in data.frame')
  }
  h=hindcasts %>%
    mutate(issue_doy = lubridate::yday(issue_date)) %>%
    mutate(issue_doy = case_when(
      issue_doy >= 305 ~ issue_doy - 365,
      TRUE ~ issue_doy
    )) 
  
  
  # save coordinates since they get weird in the next step
  if('latitude' %in% colnames(h)){
    site_info = h %>%
      select(site_id, latitude, longitude) %>%
      distinct()
  }
  
  if(fill_in_all_doys){
    # fills in predictions for every doy. 
    # ie. if there was a hindcast on doy 20 and 25. Then this copies the doy 20 prediction
    # to doy 21-24.
    h = h %>%
      complete(issue_doy=min(issue_doy):(max(issue_doy)), nesting(!!!rlang::syms(hindcast_prediction_levels))) %>%
      arrange(issue_doy) %>%
      group_by(!!!rlang::syms(hindcast_prediction_levels)) %>%
      mutate(doy_prediction = zoo::na.locf(doy_prediction, na.rm=FALSE),
             doy_observed = zoo::na.locf(doy_observed, na.rm=FALSE),
             issue_date = zoo::na.locf(issue_date, na.rm=FALSE)) %>%
      ungroup()
  }
  
  # put coordinates back in
  if('latitude' %in% colnames(h)){
    h = h %>%
      select(-latitude, -longitude) %>%
      left_join(site_info, by='site_id')
  }
  
  h = h %>%
    mutate(lead_time = issue_doy - doy_observed)
  
  return(h)
}
