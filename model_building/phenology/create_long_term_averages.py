from pyPhenology import models, utils
import pandas as pd
import numpy as np
from tools import tools
import xarray as xr
import glob
import datetime

#############
# This script uses the full phenology models, and fits them to 20 years
# of past prism data to get a long term average
# Produces an NC file of species x phenophase  x lat x lon with variables
# mean and sd representing the avg DOY and standard deviation.
#############


config = tools.load_config()
prediction_jobs = 1
forecast_version_to_use = 4

all_species_info = pd.read_csv(config['species_list_file'])

phenology_model_metadata = pd.read_csv(config['phenology_model_metadata_file'])

# Land mask for use as reference in spatial stuff
land_mask = xr.open_dataset(config['mask_file'])

observation_filenames = glob.glob(config['historic_observations_folder']+'yearly/prism_tmean*')

historic_temperature = xr.open_mfdataset(observation_filenames)

prior_years = pd.DatetimeIndex(historic_temperature.time.values).year.unique().values
prior_years = np.sort(prior_years)

today = datetime.datetime.today().date()


for y in prior_years[1:3]:
    this_year_predictions = None
    
    #################
    # Setup dates
    jan1 = tools.string_to_date(str(y)+'0101')
    nov1 = tools.string_to_date(str(y-1)+'1101')
    dec1 = tools.string_to_date(str(y)+'1201')

    date_range=pd.date_range(nov1, dec1, freq = '1D')

    # make a DOY mapping for the specific dates, where Jan.1 = DOY 1
    doy_series =  pd.TimedeltaIndex(date_range - jan1, freq='D').days.values

    ################
    # Load this years climate data
    this_year_temperature = historic_temperature.sel(time = date_range)
    this_year_temperature.load()

    for i, species_info in enumerate(all_species_info.to_dict('records')[0:4]):
        
        print('processing {y} - species {n}/{N}'.format(y=y,
                                                        n=i,
                                                        N=len(all_species_info)))
        ###############
        # Species specific info
        this_spp = species_info['species']
        this_phenophase = species_info['Phenophase_ID']
        species_model_info = phenology_model_metadata.query('species == @this_spp & \
                                                            Phenophase_ID == @this_phenophase & \
                                                            forecast_version == @forecast_version_to_use').to_dict('records')
        n_model_entries = len(species_model_info)
        if n_model_entries == 0:
            print('No model found: {s} - {p} - forecast version {f}'.format(s = this_spp,
                                                                            p = this_phenophase,
                                                                            f = forecast_version_to_use))
            continue
        if n_model_entries > 1:
            raise RuntimeError('{n} models found for {s}-{p}-v{f}'.format(s = this_spp,
                                                                            p = this_phenophase,
                                                                            f = forecast_version_to_use))
        
    
        try:
            pheno_model = utils.load_saved_model(config['phenology_model_folder'] + species_model_info[0]['model_file'])
        except:
            continue
    
        # Make the weighted ensemble unweighted
        pheno_model.weights[:] = 1 / len(pheno_model.weights)

        ################
        # Make the prediction
        prediction = pheno_model.predict(predictors={'temperature':this_year_temperature.tmean.values,
                                                     'doy_series': doy_series},
                                         n_jobs=prediction_jobs)
    
        ###############
        # Save
        
        # add 2 axis for species/phenophase/year
        prediction = np.expand_dims(prediction, 0)
        prediction = np.expand_dims(prediction, 0)
        prediction = np.expand_dims(prediction, 0)
        
        species_year_array = xr.Dataset(data_vars = {'doy_prediction':(('species','phenophase','year', 'lat','lon'), prediction)},
                                      coords = {'species':[this_spp], 'phenophase':[this_phenophase],'year':[y],
                                              'lat':land_mask.lat, 'lon':land_mask.lon})
        if this_year_predictions is None:
            this_year_predictions = species_year_array
        else:
            this_year_predictions = xr.merge([this_year_predictions, species_year_array])


    this_year_filename = config['long_term_average_folder'] + 'phenology_{y}.nc'.format(y=y)
    this_year_predictions.to_netcdf(this_year_filename,
                                    encoding = {'doy_prediction':{'zlib':True,
                                                                  'complevel':4, 
                                                                  'dtype':'int32', 
                                                                  'scale_factor':0.001,  
                                                                  '_FillValue': -9999}})


# re-open all the saved files in chunks so it doesn't destroy memory
all_predictions = xr.open_mfdataset(config['long_term_average_folder'] + 'phenology_*.nc', 
                                    chunks={'lat':200,'lon':200, 'species':20})

# Take 20 years of predictions to long term mean and sd
all_long_term_averages = xr.merge([all_predictions.doy_prediction.mean('year').to_dataset(name='doy_mean'), 
                                   all_predictions.doy_prediction.std('year').to_dataset(name='doy_sd')])

compression_details ={'doy_mean':{'zlib':True,
                                  'complevel':4, 
                                  'dtype':'int32', 
                                  'scale_factor':0.001,  
                                  '_FillValue': -9999},
                        'doy_sd':{'zlib':True,
                                  'complevel':4, 
                                  'dtype':'int32', 
                                  'scale_factor':0.001,  
                                  '_FillValue': -9999}}
    
all_long_term_averages.to_netcdf(config['data_folder'] + 'phenology_long_term_averages.nc',
                                 encoding = compression_details)



