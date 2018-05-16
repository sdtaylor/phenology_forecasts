

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
  write.table(df, filename, sep = ',', row.names = FALSE, col.names = !file.exists(filename), append = file.exists(filename))
}
