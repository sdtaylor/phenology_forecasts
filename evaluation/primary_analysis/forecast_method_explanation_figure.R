library(tidyverse)
library(patchwork)

set.seed(20)
make_temp_timeseries = function(ts_length = 60,
                                temp_initial = 20,
                                mean_trend = 0,
                                mean_sd = 0.7){
  timeseries = rep(temp_initial, ts_length)
  for(i in 2:ts_length){
    timeseries[i] = timeseries[i-1] + rnorm(1, mean = mean_trend, sd=mean_sd)
  }
  return(timeseries)
}

issue_doy = 45
final_doy = 120
num_climate_forecast_members = 5
num_past_climate_members = 20 # for 20 years 1996-2015

observed_temp = tibble(climate_member = 1,
                       doy = 1:issue_doy,
                       temp = make_temp_timeseries(ts_length = issue_doy, temp_initial = -3, mean_trend = 0.4))

##############
get_historic_member = function(member_id){
  tibble(climate_member = member_id,
         doy = 1:final_doy, 
         temp = make_temp_timeseries(ts_length = final_doy, 
                                     temp_initial = rnorm(1, mean = 3, sd=7)))
}

historic_temps = map_dfr(1:num_past_climate_members, get_historic_member)
historic_temps$source = 'historic'
#############
get_forecast_member = function(member_id){
  # A random time series starting from the issue date and temp
  tibble(climate_member = member_id,
         doy = issue_doy:final_doy, 
         temp = make_temp_timeseries(ts_length = final_doy - issue_doy + 1, 
                                     temp_initial = rev(observed_temp$temp)[1]))
}

forecast_temps = map_dfr(1:num_climate_forecast_members, get_forecast_member)

############

y_high = max(c(forecast_temps$temp, observed_temp$temp, historic_temps$temp))
y_low  = min(c(forecast_temps$temp, observed_temp$temp, historic_temps$temp))
y_range = c(y_low, y_high)

doy_to_date = function(doy){
  d = as.Date(paste0('2018-',doy), format = '%Y-%j')
  format(d, '%b %d')
}

x_breaks = c(1,32,60,91,121)
x_labels = map_chr(x_breaks, doy_to_date)

line_size = 1

##################
get_random_palette = function(original_palette = 'Blues', n){
  original_palette_values = RColorBrewer::brewer.pal(9, original_palette)[3:9]
  generate_palette = colorRampPalette(original_palette_values)
  generate_palette(n)
}

forecast_colors = get_random_palette('RdPu',num_climate_forecast_members)
historic_climate_colors = get_random_palette('Greens', num_past_climate_members)
###################
common_theme = theme_bw() +
  theme(legend.position = 'none',
        axis.text.x = element_blank(),
        axis.text.y = element_text(size=14))

method1_plot = ggplot(forecast_temps, aes(x=doy, y=temp)) + 
  geom_line(aes(color=as.factor(climate_member)), size=line_size) +
  geom_line(data = observed_temp, color='black', size=line_size) +
  geom_vline(xintercept = issue_doy, color='black', linetype = 'dotted', size=line_size) +  
  #scale_color_manual(values = c("#E69F00", "#009E73", "#0072B2", "#D55E00", "#CC79A7")) +
  scale_color_manual(values = forecast_colors) + 
  #scale_color_brewer(palette = 'Reds', direction = 1) + 
  scale_y_continuous(limits = y_range) + 
  common_theme +
  theme(plot.title = element_text(color='black')) + 
  labs(x='',y='',title = 'A. Method 1: Integrated Observed Temperature and Climate Forecasts')

method2_plot = ggplot(filter(historic_temps, doy>=issue_doy), aes(x=doy, y=temp)) +
  geom_line(aes(color=as.factor(climate_member)), size=line_size) +
  geom_line(data = observed_temp, color='black', size=line_size) +
  geom_vline(xintercept = issue_doy, color='black', linetype = 'dotted', size=line_size) +  
  #scale_color_viridis_d(end = 0.9) +
  scale_color_manual(values = historic_climate_colors) + 
  scale_y_continuous(limits = y_range) + 
  common_theme +
  theme(plot.title = element_text(color='black')) + 
  labs(x='',y='',title = 'B. Method 2: Integrated Observed Temperature Only')

method3_plot = ggplot(historic_temps, aes(x=doy, y=temp)) +
  geom_line(aes(color=as.factor(climate_member)), size=line_size) +
  geom_vline(xintercept = issue_doy, color='black', linetype = 'dotted', size=line_size) +  
  scale_color_manual(values = historic_climate_colors) + 
  scale_y_continuous(limits = y_range) + 
  scale_x_continuous(breaks = x_breaks, labels = x_labels) + 
  common_theme + 
  theme(axis.text.x = element_text(size=12),
        plot.title = element_text(color='black')) +
  labs(x='',y='',title = 'C. Method 3: Long Term Climate Only')

method1_plot + 
  method2_plot +
  method3_plot +
  plot_layout(ncol = 1)


