library(tidyverse)

####################################################################
#From the NPN dataset extract the doy observations for an
#select species and specied phenophase (ie flowering vs leafout)
#distinct() to compact down multiple observations on the same day
subset_npn_data = function(this_species, this_phenophase){
  obs_subset = all_observations %>%
    filter(species==this_species, Phenophase_ID == this_phenophase) %>%
    distinct()
  
  if(nrow(obs_subset)==0){return(data.frame())}
  
  return(obs_subset)
}

###################################################################
# Prepend the root data folder to all files and folders
# specified. 
load_config = function(){
  config = yaml::yaml.load_file('config.yaml')
  
  data_folder = config$data_folder

  config_attributes = names(config)
  # Don't prepend the root data_folder
  config_attributes = config_attributes[-which('data_folder' %in% config_attributes)]
  
  for(a in config_attributes){
    is_dir = grepl('folder',a)
    is_file= grepl('file',a)
    if(is_dir | is_file){
      config[[a]] = paste0(data_folder,config[[a]])
    }
    if(is_dir){
      if(!dir.exists(config[[a]])) dir.create(config[[a]])
    }
  }
  return(config)
}


#################################################################
#Takes a data.frame in the format colnames(species, site_id, year, status, doy)
#where status is 1 or 0, and observations include *all* the observations from the dataset.
#
#Subsets this observations that were preceeded by at least one observation of status==0,
#and sets the doy as the midpoint between the first observed status==1 and the most recent
#observation.
# prior_obs_cutoff: Only use observations where the prior status=0 observation is < this amount
#                 if equal to -1 (the default) then don't enforce this. Only used in NPN data
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
    ungroup() %>%
    filter(status==0) %>%
    select(species, site_id, year, individual_id, Phenophase_ID) %>%
    mutate(has_prior_obs='yes')
  
  #Keep only observations of status==1 that were preceded by an observation of the status==0
  df_subset = df %>%
    filter(status==1) %>%
    group_by(species, site_id, year, individual_id, Phenophase_ID) %>%
    top_n(1,-doy) %>%
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
    select(species, site_id,year,doy, Phenophase_ID)
  
  return(df_subset)
}


###############################################################

##############################################################
process_extracted_prism_data = function(extracted){
  extracted = extracted %>%
    tidyr::gather(filename, temp, -site_id) %>%
    dplyr::mutate(date=stringr::word(filename, 5, 5, sep='_')) %>%
    dplyr::select(-filename)
  
  #Convert to format used in models
  
  temperature_data = extracted %>%
    mutate(date = as.Date(as.character(date), '%Y%m%d')) %>%
    mutate(year = lubridate::year(date), doy = lubridate::yday(date))
  
  #Limit temp data to fall and mid summer
  #temperature_data = temperature_data %>%
  #  filter(doy <=180 | doy >= 240)
  
  #Assign fall (begining in Oct.) temp to the next years growing season.
  #Also set Jan 1 as doy 0, anything before that as negative doy's
  temperature_data = temperature_data %>%
    mutate(year = ifelse(doy>=300, year+1, year)) %>%
    mutate(base_date = lubridate::as_date(paste0(year,'-01-01'))) %>%
    mutate(doy = date - base_date) %>%
    select(-date, -base_date)
  
  #Cuttoff to 2 decimals to save space in the csv files
  temperature_data$temp = round(temperature_data$temp, 2)
  
  return(temperature_data)
}
