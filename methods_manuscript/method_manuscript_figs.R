library(tidyverse)
library(cowplot)

forecast_data = read_csv('/home/shawn/data/phenology_forecasting/evaluation/forecast_data_2019.csv') %>%
  select(-latitude, -longitude)
observations_2019 = read_csv('/home/shawn/data/phenology_forecasting/evaluation/phenology_2019_observations.csv') %>%
  select(-latitude, -longitude) %>%
  rename(doy_observed = doy)

# Combine obserations + forecasts for all the different issue dates. 
# drop anything with missing data. which can happen when an observations is outside
# the range for a respective species.
forecast_data = forecast_data %>%
  left_join(observations_2019, by=c('site_id','Phenophase_ID','species')) %>%
  filter(complete.cases(.))

site_info = forecast_data %>%
  select(site_id, latitude, longitude ) %>%
  distinct()


forecast_data = forecast_data %>%
  left_join(site_info, by='site_id')

# TODO:
#   -add y buffer around timeseries
#   -species names as titles instead of strip text 
#   -show all npn locations
#   -add a few more

###################################################

individual_plant_info = forecast_data %>%
  select(individual_id, species,Phenophase_ID, site_id, latitude, longitude) %>%
  distinct()

focal_individuals = c(79752,13596, 182516, 91840, 25365, 98168)
#focal_individuals = c(10207, 116301, 90115, 102271, 69162, 148429,152284,87758,46645, 129991)
#focal_sites = c(19187)
timeseries_issue_dates = lubridate::ymd(c('2018-12-03','2018-12-14',
                                     '2019-01-01','2019-01-21',
                                     '2019-02-01','2019-02-17',
                                     '2019-03-01','2019-01-17'))

###################################################
doy_to_date = function(x){
  dates = as.Date(paste(2018, x,sep='-'), '%Y-%j')
  abbr  = strftime(dates, '%b %d')
  return(abbr)                                                                                                                                                       
}
capitilize = function(s){                                                                                                                              
  l = toupper(substr(s, 1,1))
  return(paste0(l,substr(s,2,nchar(s))))
}

generate_individual_timeseries = function(id){
  individual_data = forecast_data %>%
    filter(individual_id == id,
           issue_date %in% timeseries_issue_dates) %>%
    mutate(phenophase = case_when(
      Phenophase_ID==371 ~ 'Budburst',
      Phenophase_ID==501 ~ 'Flowers'
    )) %>%
    mutate(individual_label = paste0(capitilize(species),' - ',phenophase,' (Plant: ',individual_id,', Site: ',site_id,')'))
  
  plot_title = individual_data %>%
    pull(individual_label) %>%
    unique()
  
  plot_y_min = min(c(individual_data$doy_observed,individual_data$doy_prediction-individual_data$doy_sd*2)) - 10
  plot_y_max = max(c(individual_data$doy_observed,individual_data$doy_prediction+individual_data$doy_sd*2)) + 10
  ggplot(individual_data, aes(x=issue_date, y=doy_observed)) +
    #geom_point(position = position_dodge(width=10), shape=10, size=5) +
    geom_hline(aes(yintercept=doy_observed), size=1, linetype='dashed', color='black') + 
    geom_line(aes(y=doy_prediction),position = position_dodge(width=10), size=1,  color='grey60') + 
    geom_errorbar(aes(ymin=doy_prediction-(doy_sd*2), ymax=doy_prediction+(doy_sd*2)), 
                  size=1, color='grey60',
                  width=7, position = position_dodge(width=10)) +
    #scale_color_brewer(palette = 'Dark2') + 
    scale_y_continuous(labels = doy_to_date, limits=c(plot_y_min, plot_y_max)) + 
    labs(color='',x='',y='',title=plot_title) +
    theme_bw() +
    theme(legend.position = 'none',
          plot.title = element_text(size=7, margin=margin(b=0), debug = F),
          axis.text = element_text(size=6),
          strip.background = element_rect(fill='grey90'),
          panel.background = element_rect(fill = "white"),
          plot.background = element_rect(fill = "transparent", color = NA))
}

get_individual_map_points = function(individual_ids){
  forecast_data %>%
    filter(individual_id %in% individual_ids) %>%
    select(individual_id, site_id) %>%
    distinct() %>%
    left_join(site_info, by='site_id')
}
  
######################################################

basemap = map_data('state')

individual_points = get_individual_map_points(focal_individuals)
baseplot = ggplot() + 
  geom_polygon(data = basemap, aes(x=long, y = lat, group = group), fill=NA, color='grey40', size=0.8) +
  #geom_point(data=individual_points, aes(x=longitude, y=latitude, color=as.factor(individual_id)), shape=17, size=4) + 
  #ggrepel::geom_label_repel(data=individual_points, aes(x=longitude, y=latitude, label=individual_id,color=as.factor(individual_id))) + 
  geom_point(data=site_info, aes(x=longitude, y=latitude), shape=1, stroke=1.5, size=3, color='grey60') + 
  theme_bw() +
  coord_fixed(1.3) +  
  theme(panel.background = element_blank(),
        panel.border = element_blank(),
        panel.grid.major = element_blank(),
        panel.grid.minor = element_blank(),
        axis.ticks = element_blank(),
        axis.text = element_blank(),
        axis.title = element_blank(),
        legend.position = 'blank') +
  labs(x='',y='')

focal_individuals = c(79752,13596, 182516, 91840, 25365, 98168)

timeseries79752 = generate_individual_timeseries(79752)
timeseries25365 = generate_individual_timeseries(25365)
timeseries13596 = generate_individual_timeseries(13596)
timeseries182516 = generate_individual_timeseries(182516)
timeseries91840 = generate_individual_timeseries(91840)
timeseries98168 = generate_individual_timeseries(98168)

connecting_lines = tribble(
  ~individual_id, ~x_start, ~y_start, ~x_end, ~y_end,
  79752,          0.512,      0.61,      0.6,   0.705,
  25365,          0.508,      0.435,      0.45,    0.365,
  13596,          0.57,      0.38,      0.61,    0.32,
  182516,         0.36,      0.615,      0.32,    0.705,
  91840,          0.358,      0.527,       0.332,    0.54,
  98168,          0.56,      0.493,      0.64,    0.49,
  NA, NA, NA, NA, NA
)

full_map_plot = ggdraw() + 
  draw_plot(baseplot, scale=0.4) +
  geom_segment(data=connecting_lines, aes(x=x_start, y=y_start, xend=x_end, yend=y_end), size=1) + 
  draw_plot(timeseries79752, x=0.5, y=0.6, width = 0.4, height = 0.3, scale=.8) +
  draw_plot(timeseries25365, x=0.1, y=0.13, width = 0.4, height = 0.3, scale=.8) +
  draw_plot(timeseries13596, x=0.55, y=0.13, width = 0.4, height = 0.3, scale=.8) +
  draw_plot(timeseries182516, x=0.1, y=0.6, width = 0.4, height = 0.3, scale=.8) +
  draw_plot(timeseries91840, x=-0.02, y=0.4, width = 0.4, height = 0.3, scale=.8) +
  draw_plot(timeseries98168, x=0.58, y=0.33, width = 0.4, height = 0.3, scale=.8) +
  #scale_x_continuous(breaks=seq(0,1,0.1)) +
  #scale_y_continuous(breaks=seq(0,1,0.1)) + 
  #theme(panel.grid.major = element_line(color='#56B4E9', size=0.3)) +
  geom_blank()

ggsave('methods_manuscript/map_figure.png', plot=full_map_plot, width = 30, height = 15, units = 'cm', dpi = 500)
  

################################
################################
# plot of all ~400 timeseries of predictions
giant_plot = forecast_data %>%
  mutate(individual_label = paste(species,individual_id,'(',round(latitude,1),round(longitude,2),')')) %>%
ggplot(aes(x=issue_date, y=doy_observed, color=as.factor(Phenophase_ID))) +
  #geom_point(position = position_dodge(width=10), shape=10, size=5) +
  geom_hline(aes(yintercept=doy_observed, color=as.factor(Phenophase_ID)), size=1, linetype='dashed') + 
  geom_line(aes(y=doy_prediction),position = position_dodge(width=10), size=1) + 
  geom_errorbar(aes(ymin=doy_prediction-(doy_sd*2), ymax=doy_prediction+(doy_sd*2)), 
                size=1,
                width=7, position = position_dodge(width=10)) +
  scale_color_brewer(palette = 'Dark2') + 
  scale_y_continuous(labels = doy_to_date) + 
  labs(color='',x='',y='') +
  facet_wrap(~individual_label, scales='free_y') + 
  theme_bw() +
  theme(legend.position = 'none',
        plot.title = element_text(size=7, margin=margin(b=0), debug = F),
        axis.text = element_text(size=6),
        strip.background = element_rect(fill='grey90'))

ggsave('methods_manuscript/all_2019_timeseries.png', plot=giant_plot, width=120, height = 80, units = 'cm', dpi=200)


################################
################################
# density plots of absolute errors

error_plot_issue_dates = lubridate::ymd(c('2018-12-03',
                                          '2019-01-01',
                                          '2019-02-01',
                                          '2019-03-01',
                                          '2019-03-25'))


forecast_data %>%
  filter(issue_date %in% error_plot_issue_dates, species=='acer rubrum') %>%
  mutate(absolute_error = doy_prediction - doy_observed) %>%
ggplot(aes(x=absolute_error, fill=species)) +
  geom_histogram() +
  scale_fill_viridis_d() +
  #geom_density() + 
  geom_vline(xintercept=0, color='red') +
  facet_wrap(~issue_date, ncol=2) +
  theme(legend.position = 'none')
