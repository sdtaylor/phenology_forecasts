library(rnpn)
library(docopt)
library(tidyverse)
source('phenology_observation_functions.R')

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

args$local_obs_file = '/home/shawn/data/phenology/npn_core/status_intensity_observation_data.csv'
args$local_site_file= '/home/shawn/data/phenology/npn_core/ancillary_site_data.csv'

if(args$data_source=='local_file'){
  #The raw npn data.
  all_observations = read_csv(args$local_obs_file) %>%
    select(site_id = Site_ID, individual_id = Individual_ID, Phenophase_ID, Observation_Date, status = Phenophase_Status,
           intensity_id = Intensity_Category_ID, intensity = Intensity_Value, Genus, Species) %>%
    mutate(species= tolower(paste(Genus,Species,sep=' ')), 
           year   = lubridate::year(Observation_Date),
           doy    = lubridate::yday(Observation_Date))
  
  all_sites = read_csv(args$local_site_file)
  
  for(i in 1:nrow(species_list)){
    species_info = species_list[i,]

    if(!isTRUE(species_info$observation_downloaded) | args$update_mode=='all'){
      species_data = all_observations %>%
        filter(species == species_info$species, Phenophase_ID==species_info$Phenophase_ID)
      
      if(nrow(species_data)==0){
        print(paste('Species has no data: ',species_info$species, species_info$Phenophase_ID))
        next
      }
      
      # Only keep positive observations that were  preceeded via a negative observation
      # with 30 days. And transform the observation date to the midpoint of those to dates.
      processed_data = process_phenology_observations(species_data, prior_obs_cutoff = 30)
      
      if(nrow(processed_data)==0){
        print(paste('Species/phenophase has no data after processing: ',species_info$species, species_info$Phenophase_ID))
        next
      }
    
      species_observation_file = paste(species_info$species, species_info$Phenophase_ID,sep='_')
      species_observation_file = paste0(species_observation_file,'.csv')
      species_observation_file = gsub(' ','_',species_observation_file)
      
      write_csv(processed_data, paste0(config['phenology_observations_folder'],species_observation_file))
      
      species_info$observation_downloaded=TRUE
      species_info$download_date=today
      species_info$n_observations=nrow(processed_data)
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



