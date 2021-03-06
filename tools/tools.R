

###################################################################
# Prepend the root data folder to all files and folders
# specified. 
load_config = function(){
  config = yaml::yaml.load_file('config.yaml')
  
  hostname = Sys.info()['nodename']
  # Check if we're on a hipergator node,
  # which can have many different prefixes.
  if(grepl('ufhpc', hostname)){
    hostname = 'ufhpc'
  }
  
  if(hostname %in% names(config$data_folder)){
    data_folder = config$data_folder[hostname][[1]]
  } else {
    data_folder = config$data_folder['default'][[1]]
  }
  
  config$data_folder = data_folder
  
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


#######################################################################
# Get the current growing season. ie. 2018 for all dates 2017-11-1 to 2018-10-30
current_growing_season = function(){
  config=load_config()
  today = Sys.Date()
  year = lubridate::year(today)
  season_begin = as.Date(paste(year,config$season_month_begin,config$season_day_begin,sep='-'))
  if(today > season_begin){
    year = year+1
  }
  return(year)
}

###################################################################
#Appending a csv without re-writing the header.
append_csv=function(df, filename){
  readr::read_csv(filename) %>%
    bind_rows(df) %>%
    readr::write_csv(filename)
}
