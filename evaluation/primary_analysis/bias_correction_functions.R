library(tidyverse)
library(gbm)

create_error_model = function(df, model_predictors, model_response = 'error', 
                              n.trees = 5000, interaction.depth = 4, shrinkage = 0.01) {
  
  df$Phenophase_ID = as.factor(df$Phenophase_ID)
  df$species = as.factor(df$species)
  if('phenology_model' %in% colnames(df)) {
    df$phenology_model = as.factor(df$phenology_model)
  }
  df$year = as.factor(df$year)
  
  model_formula = as.formula(paste0(model_response,'~',paste(model_predictors, collapse = '+')))
  
  m = gbm(model_formula,
          n.trees = n.trees, interaction.depth = interaction.depth, shrinkage = shrinkage,
          data=df)
  return(m)
}


apply_bias_model = function(df, error_model, n.trees=5000){
  # This adds a column, prediction type, either original or corrected.
  df %>%
    mutate(error_bias = predict(error_model, n.trees = n.trees, newdata = .)) %>%
    mutate(corrected = doy_prediction - error_bias) %>%
    rename(original = doy_prediction) %>%
    gather(bias_correction, doy_prediction, corrected, original) 
  
}
