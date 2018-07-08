#library(rnpn)
library(docopt)
library(tidyverse)
source('tools/tools.R')
source('tools/npn_data_tools.R')

config=load_config()

################################################
# Define CLI usage
'
Usage:
  download_species_observations.R [options]
Options:
  --update_mode=string      How to update species entries. Either all of them, or only newly
                            added ones (the default) [default: empty]
  --data_source=string      Either "local_file" or "api". A local file the downloaded NPN observation file,
                            while api uses the NPN file. File settings are required for local_file [default: local_file]
  --local_obs_file=FILE     Path to the local NPN observation file
  --local_site_file=FILE    Path to the local NPN site file

' -> d
args <- docopt(d)
################################################

# This will be read from a file at some point
# species_list = data.frame(species=c('fragaria virginiana','acer rubrum'),
#                           Phenophase_ID=c(501,371),
#                           observation_downloaded=NA,
#                           download_date=NA,
#                           n_observations=NA,
#                           download_source=NA,
#                           observation_file=NA)

species_list = read_csv(config$species_list_file)

today = as.character(Sys.Date())

args$local_obs_file = paste0(config$data_folder,'prior_years_npn_data/individual_phenometrics_data.csv')
args$local_site_file= paste0(config$data_folder,'prior_years_npn_data/ancillary_site_data.csv')

if(args$data_source=='local_file'){
  #The raw npn data.
  all_observations = read_csv(args$local_obs_file) 
  
  # Drop any conflicts where multiple observers disagree, or single observers
  # mark multiple onsets
  all_observations = all_observations %>%
    filter(!Observed_Status_Conflict_Flag %in% c("MultiObserver-StatusConflict","OneObserver-StatusConflict")) %>%
    filter(Multiple_FirstY==0)
  
  # Keep only observations that had a prior 'no' within 30 days
  all_observations = all_observations %>%
    filter(NumDays_Since_Prior_No >0, NumDays_Since_Prior_No<=30)
  
  # Correct observed date as midpoint between 1st 'no' and  most prior 'no'
  all_observations$First_Yes_DOY = ceiling(with(all_observations, First_Yes_DOY - (NumDays_Since_Prior_No/2)))
  
  # Rename to variables I like
  all_observations = all_observations %>%
    select(site_id = Site_ID, individual_id = Individual_ID, Phenophase_ID, Genus, Species, 
           latitude=Latitude, longitude=Longitude,
           year=First_Yes_Year, doy=First_Yes_DOY) %>%
    mutate(species= tolower(paste(Genus,Species,sep=' '))) 
  
  # Add in a unique observation ID for every species and phenophase
  all_observations = all_observations %>%
    group_by(species, Phenophase_ID) %>%
    mutate(observation_id = 1:n()) %>%
    ungroup()
  
  # Sanity check. No individual plant should have > 1 doy a year for any phenophase
  individual_phenophase_obs = all_observations %>% 
    group_by(individual_id, year, Phenophase_ID) %>% 
    tally()
  if(any(individual_phenophase_obs$n>1)) stop('> 1 observations/year/phenophase/individual')
  
  all_sites = read_csv(args$local_site_file)
  
  for(i in 1:nrow(species_list)){
    species_info = species_list[i,]

    if(!isTRUE(species_info$observation_downloaded) | args$update_mode=='all'){
      
      species_data = all_observations %>%
        filter(species == species_info$species, Phenophase_ID==species_info$Phenophase_ID)
      
      if(nrow(species_data)==0){
        print(paste('Species/phenophase has no data after processing: ',species_info$species, species_info$Phenophase_ID))
        next
      }
      
      species_observation_file = paste(species_info$species, species_info$Phenophase_ID,sep='_')
      species_observation_file = paste0(species_observation_file,'.csv')
      species_observation_file = gsub(' ','_',species_observation_file)
      
      write_csv(species_data, paste0(config['phenology_observations_folder'],species_observation_file))
      
      species_info$observation_downloaded=TRUE
      species_info$download_date=today
      species_info$n_observations=nrow(species_data)
      species_info$download_source='local'
      species_info$observation_file = species_observation_file
      
      species_list[i,] = species_info
      print(paste('Succesfully processed species - phenophase: ',species_info$species, species_info$Phenophase_ID))
      
      
    } else {
      print(paste('Skipping already downloaded species: ',species_info$species, species_info$Phenophase_ID))
    }
  }
  
  
} else if(args$data_source=='api'){
  # download the api observations
  stop('npn api download not implemented  yet')
} else {
  stop(paste0('Unknown data source option: ',args$data_source))
}

write_csv(species_list, config$species_list_file)



