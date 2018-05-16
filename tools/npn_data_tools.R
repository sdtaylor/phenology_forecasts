library(tidyverse)

#################################################################
#Takes a data.frame in the format colnames(species, site_id, year, status, doy)
#where status is 1 or 0, and observations include *all* the observations from the dataset.
#
#Subsets this observations that were preceeded by at least one observation of status==0,
#and sets the doy as the midpoint between the first observed status==1 and the most recent
#observation.
# prior_obs_cutoff: Only use observations where the prior status=0 observation is < this amount
#                 if equal to -1 (the default) then don't enforce this. Only used in NPN data
#################################################################
process_phenology_observations = function(df, prior_obs_cutoff=-1){
  #Add an observation ID for each unique series
  df = df %>%
    arrange(doy) %>%
    group_by(species, site_id, year, individual_id, Phenophase_ID) %>%
    mutate(obs_num = 1:n()) %>%
    ungroup()
  
  #site,year,species where a status==0 was the first observation in a year
  phenophase_0 = df %>%
    group_by(species, site_id, year, individual_id, Phenophase_ID) %>%
    top_n(1, -doy) %>%
    filter(row_number()==1) %>%
    ungroup() %>%
    filter(status==0) %>%
    select(species, site_id, year, individual_id, Phenophase_ID) %>%
    mutate(has_prior_obs='yes')
  
  #Keep only observations of status==1 that were preceded by an observation of the status==0
  df_subset = df %>%
    filter(status==1) %>%
    group_by(species, site_id, year, individual_id, Phenophase_ID) %>%
    top_n(1,-doy) %>%
    filter(row_number()==1) %>% # some trees have multiple
    ungroup() %>%
    left_join(phenophase_0, by=c('species','site_id','year','individual_id','Phenophase_ID')) %>%
    filter(has_prior_obs=='yes') %>% 
    select(-status, -has_prior_obs) 
  
  #Get the doy for the most recent observation, which should be status==0
  prior_observations = df_subset %>%
    mutate(obs_num = obs_num-1) %>%
    select(-doy) %>%
    left_join(df, by=c('species','site_id','year','obs_num', 'individual_id', 'Phenophase_ID')) %>%
    select(species, site_id, year, individual_id, doy_prior = doy, Phenophase_ID)
  
  df_subset = df_subset %>%
    left_join(prior_observations, by=c('species','site_id','year','individual_id','Phenophase_ID')) %>%
    mutate(doy_difference = doy-doy_prior)
  
  #Sanity check. No negative numbers, which would happen if doy_prior was larger than doy
  if(any(df_subset$doy_difference < 0, na.rm=T)){stop('doy_prior larger than doy')}
  
  if(prior_obs_cutoff>0){
    df_subset = df_subset %>%
      filter(doy_difference < prior_obs_cutoff)
  }
  
  #Final calc and select columns used in the python modeling code
  df_subset = df_subset %>%
    filter(!is.na(doy_difference)) %>%
    mutate(doy = round(doy_difference/2 + doy_prior)) %>%
    select(species, site_id,year,doy, Phenophase_ID, individual_id)
  
  return(df_subset)
}


###############################################################
# From the  output of raster::extract(), but everything into
# the format: year,doy,site_id,temperature
##############################################################
process_extracted_prism_data = function(extracted, winter_doy_begin){
  extracted = extracted %>%
    tidyr::gather(filename, temperature, -site_id) %>%
    dplyr::mutate(date=stringr::word(filename, 5, 5, sep='_')) %>%
    dplyr::select(-filename)
  
  #Convert to format used in models
  
  temperature_data = extracted %>%
    mutate(date = as.Date(as.character(date), '%Y%m%d')) %>%
    mutate(year = lubridate::year(date), doy = lubridate::yday(date))
  # To have temperature represented as a constant julian day, the fall months
  # essentially need to be repeated twice. For example. Dec. 1, 2014 will become
  # doy -31 for the 2015 season, but will *also* be doy 335 for the 2014 season.
  winter_buffer = temperature_data %>%
    filter(doy>=winter_doy_begin)

  #Assign fall (begining in Oct.) temp to the next years growing season.
  #Also set Jan 1 as doy 1, anything before that as negative doy's
  temperature_data = temperature_data %>%
    mutate(year = ifelse(doy>=winter_doy_begin, year+1, year)) %>%
    bind_rows(winter_buffer) %>%
    mutate(base_date = as.Date(paste0(year,'-01-01'))) %>%
    mutate(doy = (date - base_date) + 1) %>% # Add 1 to ensure jan 1 = doy 1
    select(-date, -base_date)
  
  #Cuttoff to 2 decimals to save space in the csv files
  temperature_data$temperature = round(temperature_data$temperature, 2)
  
  return(temperature_data)
}
