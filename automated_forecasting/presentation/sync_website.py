import os
import subprocess
import glob
from random import shuffle
import datetime

from tools import tools, api_client
import pandas as pd

config = tools.load_config()

# Sync static  images and image metadata to the website on google cloud storage

def get_available_stuff():
    current_season=tools.current_growing_season(config)
    
    image_metadata = pd.read_csv(config['phenology_forecast_figure_metadata_file'])
    
    # Sort by issue date and then species so they are displayed correctly in the dropdown
    image_metadata['issue_date_object']=pd.DatetimeIndex(image_metadata.issue_date)
    image_metadata.sort_values(['issue_date_object','species'], inplace=True)
    
    ###############################
    # Keep only images from the current growing season
    image_metadata = image_metadata[image_metadata.forecast_season == int(current_season)]
    
    ###############################
    
    # Create menu items with a pretty display name and an internal code
    ####################
    most_recent_date = datetime.datetime.strptime('2000-01-01','%Y-%m-%d')
    available_issue_dates=image_metadata[['issue_date','forecast_season']].drop_duplicates().copy()
    available_issue_dates['display_text'] = pd.to_datetime(available_issue_dates.issue_date).dt.strftime('%b %d, %Y')

    # while the  latest available  forecast is displayed by the django view,
    # the "default" entry is still used for displaying past dates, so needs
    # an entry here.
    available_issue_dates['default']=0    
    available_issue_dates = available_issue_dates.to_dict('records')
    ####################
    available_species = []
    
    # Create display as: 'red maple (Acer rubrum)'
    image_metadata['display_text'] = image_metadata[['species','common_name']].apply(
            lambda x: '{c} ({s})'.format(c=x[1],s=x[0].capitalize()), axis=1)
    
    # change the space in the species to an underscore.
    image_metadata['species'] = image_metadata['species'].apply(lambda x: x.replace(' ','_'))
    image_metadata['default'] = 0
    
    # Get info needed for javascript menu. The value to pass around (species w/ an underscore),
    # the common/scientific name display text, and whether its the default one to show
    available_species = image_metadata[['species','display_text','default']].drop_duplicates().to_dict('records')
    
    # Set the default species to something random.
    def image_available(species, phenophase=498, most_recent_date=most_recent_date):
        matching_images = image_metadata.query('species == @species & \
                                                phenophase == @phenophase & \
                                                issue_date_object == @most_recent_date')
        return matching_images.shape[0] > 0
    
    shuffle(available_species)
    
    for species_metadata in available_species:
        if image_available(species_metadata['species']):
            species_metadata['default'] = 1
            break
    
    # Sort again to it's alphabetical by species in the website menu
    available_species = sorted(available_species, key=lambda s: s['species'])
    #####################
    
    available_phenophase = [{'phenophase':'371',
                             'display_text':'Leaves',
                             'default':1},
                            {'phenophase':'501',
                             'display_text':'Flowers',
                             'default':0},
                            {'phenophase':'390',
                             'display_text':'Ripe fruit',
                             'default':0},
                            {'phenophase':'498',
                             'display_text':'Fall colors',
                             'default':0}]

    available_forecasts = image_metadata[['issue_date','species','phenophase','prediction_image','uncertainty_image','anomaly_image']].to_dict('records')


    return (available_species, available_phenophase, 
            available_issue_dates, available_forecasts)
    
def run(update_all_images=False, metadata_only=False):
        
    # sync the local static image directory and the one on the remote server
    if update_all_images:
        subprocess.call(['rsync','-av',
                         '-e ssh -i /home/shawn/.ssh/phenology_box.cer',
                         config['phenology_forecast_figure_folder'],
                         'ubuntu@phenology.naturecast.org:~/projects/phenology_forecasts_app/static/main/images/'])
    
    ###########################################
    # update image/forecast metadata on the django app
    client = api_client.PhenologyForecastAPIClient(hostname='https://phenology.naturecast.org/api/',
                                                   credential_file='/home/shawn/.phenology_naturecast_org_api_auth.yaml')
    client.login()
    
    # get everything currently on the django site
    current_issue_dates = pd.DataFrame(client.issue_date_list())
    current_species = pd.DataFrame(client.species_list())
    current_forecasts = pd.DataFrame(client.forecast_list())
    
    # whats currently on the server that processes forecasts
    available_species, available_phenophases, available_issue_dates, available_forecasts = get_available_stuff()
    
    for x in available_species:
        if current_species.empty or x['species'] not in current_species.species.tolist():
            client.species_create(x)
    
    for x in available_issue_dates:
        if current_issue_dates.empty or x['issue_date'] not in current_issue_dates.issue_date.tolist():
            client.issue_date_create(x)
    
    # make sure any new species and issue dates get refreshed
    client._load_current_entries()
    
    for x in available_forecasts:
        if current_forecasts.empty or x['prediction_image'] not in current_forecasts.prediction_image.tolist():
            client.forecast_create(x)

if __name__=='__main__':
    run()
