# This creates the json file which stores all info for populating
# the dropdown menus on the website. 
import pandas as pd
from tools import tools
import json
import datetime
from random import shuffle

def run():

    config = tools.load_config()
    
    current_season=tools.current_growing_season(config)
    
    image_metadata = pd.read_csv(config['phenology_forecast_figure_metadata_file'])
    
    # Sort by issue date and then species so they are displayed correctly in the dropdown
    image_metadata['issue_date_object']=pd.DatetimeIndex(image_metadata.forecast_issue_date)
    image_metadata.sort_values(['issue_date_object','species'], inplace=True)
    
    ###############################
    # Keep only images from the current growing season
    image_metadata = image_metadata[image_metadata.forecast_season == int(current_season)]
    
    ###############################
    
    # Create menu items with a pretty display name and an internal code
    ####################
    most_recent_date = datetime.datetime.strptime('2000-01-01','%Y-%m-%d')
    available_issue_dates=[]
    for d in image_metadata.forecast_issue_date.unique().tolist():
        d_object = datetime.datetime.strptime(d, '%Y-%m-%d')
        available_issue_dates.append({'display_text':d_object.strftime('%b %d, %Y'),
                                      'value':d})
        
        if d_object > most_recent_date:
            most_recent_date=d_object
    
    # Default menu item is the most recent issue date
    for date_metadata in available_issue_dates:
        if date_metadata['value']==most_recent_date.strftime('%Y-%m-%d'):
            date_metadata['default']=1
        else:
            date_metadata['default']=0
    
    ####################
    available_species = []
    
    # Create display as: 'red maple (Acer rubrum)'
    image_metadata['display_text'] = image_metadata[['species','common_name']].apply(
            lambda x: '{c} ({s})'.format(c=x[1],s=x[0].capitalize()), axis=1)
    
    # change the space in the species to an underscore.
    image_metadata['species'] = image_metadata['species'].apply(lambda x: x.replace(' ','_'))
    image_metadata['default'] = 0
    
    # Get info needed for javascript menu. The value to pass around (species w/ and underscore),
    # the common/scientific name display text, and whether its the default one to show
    available_species = image_metadata[['species','display_text','default']].drop_duplicates().rename(columns={'species':'value'}).to_dict('records')
    
    # Set the default species to something random.
    def image_available(species, phenophase=498, most_recent_date=most_recent_date):
        matching_images = image_metadata.query('species == @species & \
                                                phenophase == @phenophase & \
                                                issue_date_object == @most_recent_date')
        return matching_images.shape[0] > 0
    
    shuffle(available_species)
    
    for species_metadata in available_species:
        if image_available(species_metadata['value']):
            species_metadata['default'] = 1
            break
    
    # Sort again to it's alphabetical by species in the website menu
    available_species = sorted(available_species, key=lambda s: s['value'])
    #####################
    
    available_phenophase = [{'value':'371',
                             'display_text':'Leaves',
                             'default':1},
                            {'value':'501',
                             'display_text':'Flowers',
                             'default':0},
                            {'value':'498',
                             'display_text':'Fall colors',
                             'default':0}]
    
    ############
    available_images = image_metadata.img_filename.tolist()
    ##############################
    ##############################
    
    json_metadata = {'available_issue_dates':available_issue_dates,
                     'available_species':available_species,
                     'available_phenophase':available_phenophase,
                     'available_images':available_images}
    
    with open(config['phenology_forecast_figure_folder']+'image_metadata.json','w') as f:
        json.dump(json_metadata, f, indent=4)
        
    # A minified options incase this ever becomes a large file
    #with open('html/image_metadata.min.json','w') as f:
    #    json.dump(json_metadata, f, separators=(',',':'))

if __name__=='__main__':
    run()
