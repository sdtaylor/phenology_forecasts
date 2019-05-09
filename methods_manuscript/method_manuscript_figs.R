library(tidyverse)
library(cowplot)

forecast_data = read_csv('/home/shawn/data/phenology_forecasting/evaluation/forecast_data_2019.csv') %>%
  select(-latitude, -longitude) 

observations = read_csv('/home/shawn/data/phenology_forecasting/evaluation/phenology_2019_observations.csv') %>%
  select(-latitude, -longitude) %>%
  rename(doy_observed = doy)

# Combine obserations + forecasts for all the different issue dates. 
# drop anything with missing data. which can happen when an observations is outside
# the range for a respective species.
forecast_data = forecast_data %>%
  left_join(observations, by=c('site_id','Phenophase_ID','species')) %>%
  filter(complete.cases(.))

all_site_info = read_csv('/home/shawn/data/phenology_forecasting/evaluation/phenology_data_2019/ancillary_site_data.csv') %>%
  select(site_id = Site_ID, latitude=Latitude, longitude=Longitude ) %>%
  filter(longitude < -50, longitude>-130) #remove some data with bogus coordinates

evaluated_sites = all_site_info %>%
  filter(site_id %in% forecast_data$site_id)

forecast_data = forecast_data %>%
  left_join(all_site_info, by='site_id')


###################################################

individual_plant_info = forecast_data %>%
  select(individual_id, species,Phenophase_ID, site_id, latitude, longitude) %>%
  distinct()
                    
focal_individuals = c(79752,13596, 182516, 91840, 25365, 98168)

# These are the dates show in the timeseries of the map figure
timeseries_issue_dates = lubridate::ymd(c('2018-12-03','2018-12-14',
                                         '2019-01-01','2019-01-13',
                                         '2019-01-29','2019-02-17',
                                         '2019-03-01','2019-03-17',
                                         '2019-04-01','2019-04-17',
                                         '2019-05-01'))

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
    ))
    
  # Add some dummy rows so that the phenophase  get's colored correctly even when only 1
  # phenophase is available for an individual. 
  individual_data = individual_data %>%
    bind_rows(tibble(phenophase=c('Budburst','Flowers')))
  
  plot_title = individual_data %>%
    mutate(individual_title = paste0(capitilize(species))) %>%
    pull(individual_title) %>%
    unique() 
  plot_subtitle = individual_data %>%
    mutate(individual_title = paste0('(Plant: ',individual_id,', Site: ',site_id,')')) %>%
    pull(individual_title) %>%
    unique() 
  
  plot_y_min = min(c(individual_data$doy_observed,individual_data$doy_prediction-individual_data$doy_sd*2)) - 4
  plot_y_max = max(c(individual_data$doy_observed,individual_data$doy_prediction+individual_data$doy_sd*2)) + 4
  ggplot(individual_data, aes(x=issue_date, y=doy_observed, color=phenophase)) +
    #geom_point(position = position_dodge(width=10), shape=10, size=5) +
    geom_hline(aes(yintercept=doy_observed, color=phenophase), size=1, linetype='dashed') + 
    geom_line(aes(y=doy_prediction),position = position_dodge(width=3), size=1) + 
    geom_errorbar(aes(ymin=doy_prediction-(doy_sd*2), ymax=doy_prediction+(doy_sd*2), color=phenophase), 
                  size=1,
                  width=5, position = position_dodge(width=3)) +
    scale_color_manual(values=c('springgreen4','#CC79A7')) +
    #scale_color_brewer(palette = 'Dark2') + 
    scale_y_continuous(labels = doy_to_date, limits=c(plot_y_min, plot_y_max)) + 
    scale_x_date(date_labels = '%b. %e') + 
    labs(color='Phenophase',x='',y='',title=plot_title,subtitle = plot_subtitle) +
    theme_bw() +
    theme(plot.title = element_text(size=12, margin=margin(b=1),vjust = 0, debug = F),
          plot.subtitle = element_text(size=8, margin=margin(b=0), hjust = 0, debug=F),
          axis.text = element_text(size=10, color='black'),
          strip.background = element_rect(fill='grey90'),
          panel.background = element_rect(fill = "white"),
          plot.background = element_rect(fill = "transparent", color = NA))
}

get_individual_map_points = function(individual_ids){
  forecast_data %>%
    filter(individual_id %in% individual_ids) %>%
    select(individual_id, site_id) %>%
    distinct() %>%
    left_join(evaluated_sites, by='site_id')
}
  
######################################################

basemap = map_data('state')

individual_points = get_individual_map_points(focal_individuals)
baseplot = ggplot() + 
  geom_polygon(data = basemap, aes(x=long, y = lat, group = group), fill=NA, color='black', size=0.5) +
  geom_point(data=evaluated_sites, aes(x=longitude, y=latitude), shape=1, stroke=0.8, size=2, color='#0072B2') + 
  geom_point(data=all_site_info, aes(x=longitude, y=latitude), size=0.5, color='#D55E00') + 
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


# Only need the legend once, so remove it from the main timeseries plots
no_legend = theme(legend.position = 'none')

timeseries79752 = generate_individual_timeseries(79752) + no_legend
timeseries25365 = generate_individual_timeseries(25365) + no_legend
timeseries13596 = generate_individual_timeseries(13596) + no_legend
timeseries182516 = generate_individual_timeseries(182516) + no_legend
timeseries91840 = generate_individual_timeseries(91840) + no_legend
timeseries98168 = generate_individual_timeseries(98168) + no_legend

connecting_lines = tribble(
  ~individual_id, ~x_start, ~y_start, ~x_end, ~y_end,
  79752,          0.512,      0.61,      0.608,   0.725,
  25365,          0.508,      0.435,      0.43,    0.3,
  13596,          0.57,      0.38,      0.658,    0.315,
  182516,         0.36,      0.615,      0.37,    0.72,
  91840,          0.358,      0.527,       0.332,    0.54,
  98168,          0.56,      0.493,      0.7,    0.508,
  NA, NA, NA, NA, NA
)

timeseries_legend = cowplot::get_legend(generate_individual_timeseries(25365) +
  theme(legend.background = element_rect(fill=NA, color='black', size=0.25),
        legend.key.width = unit(10,'mm'),
        legend.key.height = unit(6,'mm'),
        legend.title = element_text(size=14),
        legend.text = element_text(size=12)))

full_map_plot = ggdraw() + 
  draw_plot(baseplot, scale=0.4) +
  geom_segment(data=connecting_lines, aes(x=x_start, y=y_start, xend=x_end, yend=y_end), size=1, color='grey30') + 
  draw_plot(timeseries79752, x=0.5, y=0.6, width = 0.4, height = 0.4, scale=.8) +
  draw_plot(timeseries25365, x=0.1, y=0.02, width = 0.4, height = 0.4, scale=.8) +
  draw_plot(timeseries13596, x=0.55, y=0.02, width = 0.4, height = 0.4, scale=.8) +
  draw_plot(timeseries182516, x=0.1, y=0.6, width = 0.4, height = 0.4, scale=.8) +
  draw_plot(timeseries91840, x=-0.02, y=0.3, width = 0.4, height = 0.4, scale=.8) +
  draw_plot(timeseries98168, x=0.58, y=0.29, width = 0.4, height = 0.4, scale=.8) +
  draw_plot(timeseries_legend, x=0.45, y=0.15, width=0.15, height=0.15, scale=0.2) +
  geom_blank()

ggsave('methods_manuscript/figure_3_map_figure.png', plot=full_map_plot, width = 30, height = 15, units = 'cm', dpi = 500)
  

################################
################################
# plot of all ~400 timeseries of predictions
# giant_plot = forecast_data %>%
#   mutate(individual_label = paste(species,individual_id,'(',round(latitude,1),round(longitude,2),')')) %>%
# ggplot(aes(x=issue_date, y=doy_observed, color=as.factor(Phenophase_ID))) +
#   #geom_point(position = position_dodge(width=10), shape=10, size=5) +
#   geom_hline(aes(yintercept=doy_observed, color=as.factor(Phenophase_ID)), size=1, linetype='dashed') + 
#   geom_line(aes(y=doy_prediction),position = position_dodge(width=10), size=1) + 
#   geom_errorbar(aes(ymin=doy_prediction-(doy_sd*2), ymax=doy_prediction+(doy_sd*2)), 
#                 size=1,
#                 width=7, position = position_dodge(width=10)) +
#   scale_color_brewer(palette = 'Dark2') + 
#   scale_y_continuous(labels = doy_to_date) + 
#   labs(color='',x='',y='') +
#   facet_wrap(~individual_label, scales='free_y') + 
#   theme_bw() +
#   theme(legend.position = 'none',
#         plot.title = element_text(size=7, margin=margin(b=0), debug = F),
#         axis.text = element_text(size=6),
#         strip.background = element_rect(fill='grey90'))
# 
# ggsave('methods_manuscript/all_2019_timeseries.png', plot=giant_plot, width=120, height = 80, units = 'cm', dpi=200)


################################
################################
# timeseries of uncertainty
forecast_metrics = forecast_data %>%
  group_by(issue_date) %>%
  summarize(mean_uncertainty = mean(doy_sd),
            rmse = sqrt(mean(doy_observed - doy_prediction)^2)) %>%
  ungroup() %>%
  gather(metric, metric_value, mean_uncertainty, rmse)
forecast_metrics$metric = factor(forecast_metrics$metric, levels=c('rmse','mean_uncertainty'), labels=c('RMSE','Average S.D.'))

metric_plot = ggplot(forecast_metrics, aes(x=issue_date, y=metric_value, color=metric)) +
  geom_point(size=3) + 
  geom_line(size=1.2) +
  scale_color_manual(values=c("grey10", "grey60",'red')) + 
  labs(x = 'Issue Date', y='', color='') +
  theme_bw() +
  theme(legend.position = c(0.15,0.15),
        legend.title = element_blank(),
        legend.key.width = unit(20,'mm'),
        legend.background = element_rect(fill='white', color='black', size=0.25),
        axis.text = element_text(size=14, color='black'),
        axis.title = element_text(size=18),
        legend.text = element_text(size=12),
        panel.background = element_rect(fill='NA'),
        plot.background = element_rect(fill='white'))

ggsave('methods_manuscript/figure_4_metric_timeseries.png', plot=metric_plot, width=20, height = 8, units = 'cm', dpi=500)

################################
################################
# timeseries boxplots of absolute errors

### 2019
error_plot_issue_dates = lubridate::ymd(c('2018-12-03','2018-12-19',
                                          '2019-01-01',"2019-01-13",
                                          '2019-02-01',"2019-02-17",
                                          '2019-03-01','2019-03-17',
                                          '2019-04-01','2019-04-17',
                                          '2019-05-01'))

mean_errors = forecast_data %>%
  filter(issue_date %in% error_plot_issue_dates) %>%
  #filter(latitude <= 35) %>%
  mutate(absolute_error = (doy_prediction - doy_observed)) %>%
  group_by(issue_date) %>%
  summarise(mae = round(mean(absolute_error),1),
            median_error = median(absolute_error)) %>%
  ungroup()

error_plot = forecast_data %>%
  filter(issue_date %in% error_plot_issue_dates) %>%
  #filter(latitude <= 35) %>%
  mutate(absolute_error = (doy_prediction - doy_observed)) %>%
ggplot(aes(x=issue_date, y=absolute_error)) + 
  geom_jitter(width = 2.5, height = 0, size=2, alpha=0.15, color='#0072B2') + 
  geom_boxplot(aes(group=issue_date), width=6, size=1, color='black',fill=NA, outlier.color = 'transparent') + 
  geom_hline(yintercept = 0, size=1, color='black', linetype='dashed') + 
  geom_label(data=mean_errors, aes(y=-55, label=mae), size=8, alpha=0.6) +
  scale_x_date(date_labels = '%b. %e') +
  theme_bw() +
  theme(axis.text = element_text(color='black', size=22),
        panel.grid = element_blank(),
        axis.title = element_text(size=30)) + 
  labs(x='Issue Date', y='Absolute Error')

ggsave('methods_manuscript/figure_5_error_timeseries.png', plot=error_plot, width=40, height = 16, units = 'cm', dpi=500)
