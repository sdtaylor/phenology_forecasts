library(tidyverse)
source('tools/tools.R')

config=load_config()

forecasted_species = read_csv('/home/shawn/data/phenology_forecasting/species_for_hindcasting.csv')

species_habit = forecasted_species %>%
  select(species,habit) %>%
  distinct() %>%
  mutate(habit = tools::toTitleCase(habit))

validation_observations = read_csv(config$phenology_current_season_observation_file) %>%
  filter(interaction(species, Phenophase_ID) %in% interaction(forecasted_species$species, forecasted_species$Phenophase_ID)) %>%
  select(-year, -latitude, -longitude) %>%
  rename(doy_observed = doy)

forecast_data = read_csv('/home/shawn/data/phenology_forecasting/validation/forecast_data.csv') %>%
  mutate(issue_doy = lubridate::yday(issue_date)) %>%
  mutate(issue_doy = ifelse(issue_date < '2018-01-01', -1* (as.Date('2018-01-01') - issue_date), issue_doy)) %>%
  select(-latitude, -longitude) 

# Drop any site if there are NA values in it's forecast timeseries. 
# Likely an issue with the cropping of the images
forecast_data = forecast_data %>%
  group_by(species, Phenophase_ID, site_id) %>%
  filter(sum(is.na(prediction))==0)

##############################################
# Create a separate Ensemble model forecast
ensemble_model_forecast = forecast_data %>%
  # Mean and variance among the 4 models
  group_by(issue_date,issue_doy, climate_ensemble, species, Phenophase_ID, site_id) %>%
  summarize(prediction_mean = sum(prediction*phenology_weight), 
            phenology_sd = sqrt(sum(phenology_weight*((prediction-prediction_mean)^2))),
            n=n()) %>%
  ungroup() %>%
  # Mean and variance among the 5 climate ensembles
  group_by(Phenophase_ID, issue_date, site_id, species, issue_doy) %>%
  summarise(doy_prediction = mean(prediction_mean),
            sum_sq = sum((prediction_mean-doy_prediction)**2),
            doy_sd = sqrt(mean(phenology_sd^2) + (sum_sq / (n()-1)))) %>%
  ungroup() %>%
  select(-sum_sq) %>%
  mutate(phenology_model='Ensemble') 


# Of the 4 base models, get their mean and SD among the climate ensembles
# base_model_forecasts = forecast_data %>%
#   group_by(Phenophase_ID,species, issue_date, issue_doy, site_id, phenology_model) %>%
#   summarise(doy_prediction = mean(prediction),
#             doy_sd = sd(prediction)) %>%
#   ungroup()


#forecast_data = base_model_forecasts %>%
#   bind_rows(ensemble_model_forecast)
forecast_data = ensemble_model_forecast

################################
# fills in a foreast for every day. 
# ie. if there were forecasts on doy 20 and 25. Then this copies the doy 20 forecast
# to doy 21-24.
forecast_data = forecast_data %>%
  complete(issue_doy=min(issue_doy):(max(issue_doy)+30), nesting(species, Phenophase_ID, site_id, phenology_model)) %>%
  arrange(issue_doy) %>%
  group_by(species, Phenophase_ID, site_id, phenology_model) %>%
  mutate(doy_prediction = zoo::na.locf(doy_prediction, na.rm=FALSE),
         doy_sd = zoo::na.locf(doy_sd, na.rm=FALSE),
         issue_date = zoo::na.locf(issue_date, na.rm=FALSE)) %>%
  ungroup()

################################

naive_forecast_data = read_csv('/home/shawn/data/phenology_forecasting/validation/naive_model_data.csv') %>%
  select(species, Phenophase_ID, site_id, 
         naive_prediction = doy_prediction, naive_prediction_sd = doy_sd)

forecast_data = forecast_data %>%
  left_join(naive_forecast_data, by=c('species','site_id','Phenophase_ID')) %>%
  left_join(validation_observations, by=c('species','site_id','Phenophase_ID'))

forecast_data = forecast_data %>%
  mutate(lead_time = (issue_doy - doy_observed))

# Dropping observations that were recorded prior to any forecasts being issued
# or have no forecast data (outside of range maps)
# forecast_data = forecast_data %>%
#   filter(issue_doy < doy_observed) %>%
#   filter(!is.na(doy_prediction))

# Only keep observations with at least 90 days of forecasts
obs_to_keep = forecast_data %>%
  group_by(species, Phenophase_ID, observation_id) %>%
  summarize(has_adequate_lead_time = min(lead_time) <= -90) %>%
  ungroup() 

forecast_data = forecast_data %>%
  left_join(obs_to_keep, by=c('species','Phenophase_ID','observation_id')) %>%
  filter(has_adequate_lead_time) %>%
  select(-has_adequate_lead_time) %>%
  filter(lead_time >= -90, lead_time <=0)
################################
# This species seems artificially high, potentially due 
# to a lot of observations at relatively few sites
forecast_data = forecast_data %>%
  filter(species != 'amelanchier grandiflora-autumnbrilliance')
################################

aggregate_forecast_error = forecast_data %>%
  #group_by(species, Phenophase_ID, phenology_model, lead_time) %>%
  group_by( phenology_model, lead_time) %>%
  summarise(naive_error = sqrt(mean((naive_prediction - doy_observed)**2)),
            forecast_error = sqrt(mean((doy_prediction - doy_observed)**2)),
            skill = 1 - (forecast_error/naive_error),
            n=n()) %>%
  ungroup()
aggregate_forecast_error$error_type = 'Overall (n=1618)'

genus_forecast_error = forecast_data %>%
  rename(genus=Genus) %>%
  mutate(genus = case_when(
    genus %in% c('Quercus','Acer','Populus','Betula') ~ genus,
    TRUE ~ 'Other'
  )) %>%
  group_by(genus, phenology_model, lead_time) %>%
  summarise(naive_error = sqrt(mean((naive_prediction - doy_observed)**2)),
            forecast_error = sqrt(mean((doy_prediction - doy_observed)**2)),
            skill = 1 - (forecast_error/naive_error),
            n=n()) %>%
  ungroup() %>%
  mutate(genus_with_n = paste0(genus,' (n=',n,')'))

habit_forecast_error = forecast_data %>%
  left_join(species_habit, by='species') %>%
  group_by(habit, phenology_model, lead_time) %>%
  summarise(naive_error = sqrt(mean((naive_prediction - doy_observed)**2)),
            forecast_error = sqrt(mean((doy_prediction - doy_observed)**2)),
            skill = 1 - (forecast_error/naive_error),
            n=n()) %>%
  ungroup() %>%
  mutate(habit_with_n = paste0(habit,' (n=',n,')'))

phenophase_forecast_error = forecast_data %>%
  group_by(Phenophase_ID, phenology_model, lead_time) %>%
  summarise(naive_error = sqrt(mean((naive_prediction - doy_observed)**2)),
            forecast_error = sqrt(mean((doy_prediction - doy_observed)**2)),
            skill = 1 - (forecast_error/naive_error),
            n=n()) %>%
  ungroup() 

phenophase_forecast_error$Phenophase_ID = factor(phenophase_forecast_error$Phenophase_ID, levels=c(501,371), labels=c('Open Flowers','Budburst'), ordered = TRUE)
phenophase_forecast_error$phenophase_with_n = with(phenophase_forecast_error, paste0(Phenophase_ID,' (n=',n,')'))

species_forecast_error = forecast_data %>%
  group_by(species,Phenophase_ID, phenology_model, lead_time) %>%
  summarise(naive_error = sqrt(mean((naive_prediction - doy_observed)**2)),
            forecast_error = sqrt(mean((doy_prediction - doy_observed)**2)),
            skill = 1 - (forecast_error/naive_error),
            n=n()) %>%
  ungroup() 
species_forecast_error$Phenophase_ID = factor(species_forecast_error$Phenophase_ID, levels=c(371,501), labels=c('Budburst','Open Flowers'))

######################################################
x_pos_line= -100
indicator_lines=data.frame(y=c(-0.05, 0.05), yend=c(-0.12, 0.12),
                           x=c(x_pos_line,x_pos_line), xend=c(x_pos_line,x_pos_line))

x_pos_text=-93
indicator_text=data.frame(y=c(-0.17, 0.17), x=x_pos_text, t=c('Worse than\n simple model','Better than\n simple model'))

ylim_high = 0.25
ylim_low  =-0.25

dark_blue_color = '#242F40'
orangish_color = '#CCA43B'
yellowish = '#EEE3AB'
whitish = '#D9CFC1'
light_text_color = 'grey90'
####
aggregate_plot = ggplot(aggregate_forecast_error, aes(x=lead_time, y=skill, color=error_type)) + 
  geom_hline(yintercept = 0,color='black', size=2) + 
  geom_line(size=4) +
  scale_color_manual(values=c(yellowish)) + 
  geom_segment(data=indicator_lines, aes(x=x, xend=xend, y=y, yend=yend),color=light_text_color, size=3, arrow = arrow(length=unit(1,'cm')),
               inherit.aes = F) +
  geom_text(data=indicator_text, aes(x=x,y=y, label=t),size=15,color=light_text_color, inherit.aes = F) +
  ylim(ylim_low, ylim_high) +
  scale_x_continuous(labels = function(x){x*-1},  limits = c(-101,8)) + 
  labs(y='Skill',x='Days until event', color='') + 
  theme_bw() +
  theme(legend.position = c(0.7,0.2),
        legend.direction = 'horizontal',
        legend.text = element_text(size=56, color=light_text_color),
        legend.key.width = unit(2,'cm'),
        legend.key.height = unit(0.5,'cm'),
        legend.key = element_rect(fill=NA),
        legend.background = element_rect(fill=dark_blue_color),
        axis.title = element_text(size=52, color='black'),
        axis.text = element_text(size=44, color='black'),
        panel.grid.major = element_line(size=1.5, color='grey40'),
        panel.grid.minor = element_blank(),
        panel.border = element_rect(size=1.8),
        panel.background = element_rect(fill=dark_blue_color),
        plot.background = element_rect(fill=yellowish, color=yellowish))

ggsave(file = 'analysis/aggregate_forecast_error.png', plot = aggregate_plot, height = 40, width = 45, units = 'cm')  
#####
phenophase_labels = phenophase_forecast_error %>%
  filter(lead_time==0)

phenophase_plot = ggplot(phenophase_forecast_error, aes(x=lead_time, y=skill, color=as.factor(phenophase_with_n))) + 
  geom_hline(yintercept = 0,color='black', size=2) + 
  geom_line(size=4) +
  scale_color_manual(values=c("#F0E442", "#D55E00")) + 
  geom_segment(data=indicator_lines, aes(x=x, xend=xend, y=y, yend=yend), size=3, color=light_text_color, arrow = arrow(length=unit(1,'cm')),
               inherit.aes = F) +
  geom_text(data=indicator_text, aes(x=x,y=y, label=t),size=15, color=light_text_color, inherit.aes = F) +
  geom_text(data=phenophase_labels, aes(x=0.5, y=skill, label=c('Budburst','Flowers')), size=12, color=light_text_color, hjust=0,nudge_x = 0) +
  ylim(ylim_low, ylim_high) +
  scale_x_continuous(labels = function(x){x*-1}, limits=c(-101,10)) + 
  labs(y='Skill',x='Days until event', color='') + 
  theme_bw() +
  theme(legend.position = c(0.67,0.2),
        legend.text = element_text(size=56, color=light_text_color),
        legend.key.width = unit(4,'cm'),
        legend.key.height = unit(1,'cm'),
        legend.key = element_rect(fill=NA),
        legend.background = element_rect(fill=dark_blue_color),
        axis.title = element_text(size=52),
        axis.text = element_text(size=44, color='black'),
        panel.grid.major = element_line(size=1.5, color='grey40'),
        panel.grid.minor = element_blank(),
        panel.border = element_rect(size=1.8),
        panel.background = element_rect(fill=dark_blue_color),
        plot.background = element_rect(fill=yellowish, color=yellowish)) + 
  guides(color=guide_legend(ncol = 1,
                            keyheight = 4,
                            reverse = TRUE))

ggsave(file = 'analysis/phenophase_forecast_error.png', plot = phenophase_plot, height = 40, width = 45, units = 'cm')  
####

genus_labels = genus_forecast_error %>%
  filter(lead_time==0) %>%
  mutate(lead_time=0.5)

genus_plot = ggplot(genus_forecast_error, aes(x=lead_time, y=skill, color=as.factor(genus_with_n))) + 
  geom_hline(yintercept = 0, color='black', size=2) + 
  geom_line(size=4) +
  scale_color_manual(values=c("#E69F00", "#009E73", "#999999", "#0072B2", "#CC79A7")) + 
  geom_segment(data=indicator_lines, aes(x=x, xend=xend, y=y, yend=yend), size=3,color=light_text_color, arrow = arrow(length=unit(1,'cm')),
               inherit.aes = F) +
  geom_text(data=indicator_text, aes(x=x,y=y, label=t),size=15,color=light_text_color, inherit.aes = F) +
  geom_text(data=genus_labels, aes(x=0.5, y=skill, label=genus), size=10, color=light_text_color, hjust=0,nudge_x = 0) +
  ylim(ylim_low, ylim_high) +
  scale_x_continuous(labels = function(x){x*-1}, limits = c(-101,8)) + 
  #ggtitle('By Genus') + 
  labs(y='Skill',x='Days until event', color='') + 
  theme_bw() +
  theme(legend.position = c(0.55,0.12),
        legend.direction = 'horizontal',
        legend.text = element_text(size=45, color=light_text_color),
        legend.key.width = unit(4,'cm'),
        legend.key.height = unit(1,'cm'),
        legend.key = element_rect(fill=NA),
        legend.background = element_rect(fill=dark_blue_color),
        axis.title = element_text(size=52, color='black'),
        axis.text = element_text(size=44, color='black'),
        panel.grid.major = element_line(size=1.5, color='grey40'),
        panel.grid.minor = element_blank(),
        panel.border = element_rect(size=1.8),
        panel.background = element_rect(fill=dark_blue_color),
        plot.background = element_rect(fill=yellowish, color=yellowish)) +
  guides(color=guide_legend(nrow=5,
                            keyheight=3))

ggsave(file = 'analysis/genus_forecast_error.png', plot = genus_plot, height = 40, width = 45, units = 'cm')  
####
habit_labels = habit_forecast_error %>%
  filter(lead_time==0)

habit_plot = ggplot(habit_forecast_error, aes(x=lead_time, y=skill, color=as.factor(habit_with_n))) + 
  geom_hline(yintercept = 0, color='black', size=2) + 
  geom_line(size=4) +
  scale_color_manual(values=c( '#8bd5cc','#cbef43')) + 
  geom_segment(data=indicator_lines, aes(x=x, xend=xend, y=y, yend=yend), size=3,color=light_text_color, arrow = arrow(length=unit(1,'cm')),
               inherit.aes = F) +
  geom_text(data=indicator_text, aes(x=x,y=y, label=t),size=15,color=light_text_color, inherit.aes = F) +
  geom_text(data=habit_labels, aes(x=0.5, y=skill, label=habit), size=15, color=light_text_color, hjust=0,nudge_x = 0) +
  ylim(ylim_low, ylim_high) +
  scale_x_continuous(labels = function(x){x*-1}, limits=c(-101,6)) + 
  #ggtitle('By Habit') + 
  labs(y='Skill',x='Days until event', color='') + 
  theme_bw() +
  theme(legend.position = c(0.6,0.2),
        legend.direction = 'horizontal',
        legend.text = element_text(size=56, color=light_text_color),
        legend.key.width = unit(4,'cm'),
        legend.key.height = unit(1,'cm'),
        legend.key = element_rect(fill=NA),
        legend.background = element_rect(fill=dark_blue_color),
        legend.spacing = unit(10,'cm'),
        axis.title = element_text(size=52, color='black'),
        axis.text = element_text(size=44, color='black'),
        panel.grid.major = element_line(size=1.5, color='grey40'),
        panel.grid.minor = element_blank(),
        panel.border = element_rect(size=1.8),
        panel.background = element_rect(fill=dark_blue_color),
        plot.background = element_rect(fill=yellowish, color=yellowish)) +
  guides(color=guide_legend(nrow=2,
                            keyheight = 4,
                            reverse = TRUE))

ggsave(file = 'analysis/habit_forecast_error.png', plot = habit_plot, height = 40, width = 45, units = 'cm')  
################
sample_sizes = species_forecast_error %>%
  select(species, Phenophase_ID, lead_time, n) %>%
  distinct()

###########################################
#### All the species with phenophase color coded
###########################################
ggplot(species_forecast_error, aes(x=lead_time, y=skill, color=Phenophase_ID)) + 
  geom_line(size=1.5) +
  scale_color_manual(values=c("#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7")) + 
  #scale_color_viridis_d() +
  #geom_segment(data=indicator_lines, aes(x=x, xend=xend, y=y, yend=yend), size=0.8, arrow = arrow(length=unit(0.25,'cm')),
  #             inherit.aes = F) +
  #geom_text(data=indicator_text, aes(x=x,y=y, label=t),size=4.5, inherit.aes = F) +
  ylim(-0.25,0.25) +
  scale_x_continuous(labels = function(x){x*-1}) + 
  geom_hline(yintercept = 0, linetype='dashed', size=1) + 
  labs(y='Skill',x='Lead time in days', color='') + 
  theme_bw() +
  facet_wrap(~species) +
  theme(legend.position = c(0.6,0.1),
        legend.direction = 'horizontal',
        legend.text = element_text(size=18),
        legend.key.width = unit(2,'cm'),
        legend.key.height = unit(0.5,'cm'),
        axis.title = element_text(size=18),
        axis.text = element_text(size=12))

sample_sizes = species_forecast_error %>%
  select(species, Phenophase_ID, n) %>%
  distinct()

########################################################

# # Get only forecast errors, staring from doy 0 that
# # # are < naive forecast
# get_good_forecasts = function(df){
#   print(paste(unique(df$species),unique(df$Phenophase_ID), unique(df$phenology_model)))
#   df  =  df %>%
#     arrange(-lead_time) %>%
#     mutate(naive_is_better = forecast_error > naive_error)
# 
#   if(all(!df$naive_is_better)){
#     return(df)
#   }
# 
#   first_lead_time_with_bad_forecast = min(which(df$naive_is_better))
# 
#   if(first_lead_time_with_bad_forecast==1){
#     return(data.frame())
#   } else {
#     return(df[1:first_lead_time_with_bad_forecast,])
#   }
# }
# 
# good_forecasts = forecast_error %>%
#   group_by(species, Phenophase_ID, phenology_model) %>%
#   do(get_good_forecasts(.)) %>%
#   ungroup()
# 
# ggplot(good_forecasts, aes(x=lead_time, y=forecast_error, color=phenology_model)) +
#   geom_line() +
#   facet_wrap(species~Phenophase_ID, scales='free_y')
#   

# #########################################################
# # lead time error of all speices
# species_forecast_error = forecast_data %>%
#   group_by(species, Phenophase_ID, phenology_model, lead_time) %>%
#   summarise(naive_error = sqrt(mean((naive_prediction - doy_observed)**2)),
#             forecast_error = sqrt(mean((doy_prediction - doy_observed)**2)),
#             skill = 1 - (forecast_error/naive_error),
#             n=n()) %>%
#   ungroup() 
# 
# for(s in unique(species_forecast_error$species)){
#   print(s)
#   #f(s == 'hamamelis virginiana') next
#   plot_data = species_forecast_error %>%
#     filter(species==s)
#   plot_sample_sizes = plot_data %>%
#     select(species, Phenophase_ID, lead_time, n) %>%
#     distinct() %>%
#     filter(lead_time%%8==0)
# 
#   #if(sample_size_371 < 10 & sample_size_501 < 10) next
# 
#   plot_data = plot_data %>%
#     gather(error_type, error, naive_error, forecast_error)
# 
# p=ggplot(plot_data, aes(x=lead_time, y=error, group=interaction(phenology_model, error_type), color=as.factor(phenology_model), linetype=as.factor(error_type))) +
#   #geom_point(size=3, alpha=0.4) +
#   geom_line(size=1) +
#   geom_text(data=plot_sample_sizes, aes(x=lead_time, y=-1, label=n),position = position_jitter(height=0.5,width=0), size=4.8, inherit.aes = F) + 
#   #geom_smooth(method='loess') +
#   #geom_hline(aes(yintercept = mean(naive_error))) +
#   #ylim(-5,1) +
#   facet_wrap(Phenophase_ID~species) +
#   #annotate('text', x=-10, y=-4.2, label=annotation_text)+
#   labs(x='lead time in days') +
#   theme(strip.text = element_text(size=12),
#         axis.text = element_text(size=14))
# #print(p)
# ggsave(file=paste0('lead_time_plots/',stringr::str_replace(s, ' ','_'),'.png'), plot=p, height = 20, width=60, units='cm')
# }

