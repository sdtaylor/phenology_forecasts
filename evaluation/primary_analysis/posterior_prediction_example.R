library(tidyverse) 
library(viridis)
library(patchwork)
source('tools/tools.R')

config = load_config()
########################################
# This script produces the following
# Figure S1: 3 histograms showing the posterior distributios for a single species,issue date, and location

########################################

hindcasts_primary_method = data.table::fread(paste0(config$data_folder,'evaluation/hindcast_data_2018.csv'))

climate_and_pheno_model_and_parameters = hindcasts_primary_method %>%
  filter(species=='acer rubrum', Phenophase_ID==371, site_id==5582, issue_date=='2018-01-02') %>%
  select(phenology_model, bootstrap, climate_member, doy_prediction) %>%
  mutate(posterior = 'C. Climate + Phenology Model + Parameter')

final_doy_prediction = mean(climate_and_pheno_model_and_parameters$doy_prediction)

climate_and_pheno_model = climate_and_pheno_model_and_parameters %>%
  group_by(climate_member, phenology_model) %>%
  summarise(doy_prediction = mean(doy_prediction)) %>%
  ungroup() %>%
  mutate(posterior = 'B. Climate + Phenology Model')

climate_only = climate_and_pheno_model %>%
  group_by(climate_member) %>%
  summarise(doy_prediction = mean(doy_prediction)) %>%
  ungroup() %>%
  mutate(posterior = 'A. Climate Only',
         phenology_model = 'All')


all_posteriors = climate_and_pheno_model_and_parameters %>%
  bind_rows(climate_and_pheno_model) %>%
  bind_rows(climate_only)

prediction_intervals = all_posteriors %>%
  group_by(posterior) %>%
  summarise(doy_prediction_sd = sd(doy_prediction),
            doy_prediction = mean(doy_prediction)) %>%
  ungroup() %>%
  mutate(upper_ci = doy_prediction + doy_prediction_sd*1.96,
         lower_ci = doy_prediction - doy_prediction_sd*1.96) %>%
  select(posterior, upper_ci, lower_ci) %>%
  gather(interval_type, doy_prediction_interval, upper_ci, lower_ci)

uncertainty_posterior_examples_fig = ggplot(all_posteriors, aes(x=doy_prediction, fill=phenology_model)) + 
  geom_histogram(bins=50) + 
  geom_vline(xintercept = final_doy_prediction, color='#D55E00', size=2) + 
  geom_vline(data = prediction_intervals, aes(xintercept = doy_prediction_interval), color='#D55E00', linetype='dashed', size=2) + 
  scale_fill_manual(values =  c("#000000", "#E69F00", "#56B4E9", "#009E73", "#0072B2")) + 
  facet_wrap(~posterior, ncol=1, scales='free_y') +
  theme_bw() +
  theme(strip.text = element_text(size=18),
        axis.text  = element_text(size=12, color='black'),
        strip.background = element_blank()) +
  labs(y='Posterior sample count', x='Posterior Prediction for Day Of Year (DOY)',
       fill  = 'Phenology Model')

ggsave('evaluation1_manuscript/figs/figS1_posterior_predictions_example.png', height=20, width=20, units='cm', dpi=150)
