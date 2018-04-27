This folder contains code to perform hindcasts from past dates. There are a few steps.



1. Make sure you have models built and referenced in the species_for_hindcasting file
set in the config

2. Set things up in the config, such as the target season, date range, ensemble size, etc.

3. Create the observed weather file with the function in hindcast_prep

4. create_past_climate_forecasts will download all the CFSv2 forecasts for 
the date range and put them in <base_folder>/past_climate_foreacasts/<date>

5. hindcasting will apply the specified models to all the dates. This can take a 
loooooooong time, especially with bootstrapped models. So it's setup to work 
on the hipergator using dask and dask distributed. 