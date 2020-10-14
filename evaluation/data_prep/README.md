#### prepare data for evaluation of phenology forecasts.
Note several of the functions used here were for some preliminary analysis and are not longer used in the primary_analysis/ scripts

process_current_season_observations.R
    put the current season (ie. newest data) NPN into the format used throughout.

extract_forecast_values.py
    for all the current season npn sites, extract the forecasted values for the
    respective species and phenophase.

load_forecast_data.R
    helper script to load the forecast data + observations for analysis.
