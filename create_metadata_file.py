# This creates the json file which stores all info for populating
# the dropdown menus on the website. 

import pandas as pd
from tools import tools
import json
import datetime

config = tools.load_config()

image_metadata = pd.read_csv(config['phenology_forecast_figure_metadata_file'])

###############################
# TODO: Here is were I'll delete older stuff after some period of time, like
# 2-3 months or something.
###############################

json_metadata=[]
# Create menu items with a pretty display name and an internal code
####################
available_issue_dates=[]
for d in image_metadata.forecast_issue_date.unique().tolist():
    d_object = datetime.datetime.strptime(d, '%Y-%m-%d')
    available_issue_dates.append({'issue_date_display':d_object.strftime('%b %d, %Y'),
                                  'issue_date':d})
####################
available_species = []

# Create display as: 'red maple (acer rubrum)'
image_metadata['species_display'] = image_metadata[['species','common_name']].apply(
        lambda x: '{c} ({s})'.format(c=x[1],s=x[0]), axis=1)

# change the space in the species to an underscore.
image_metadata['species'] = image_metadata['species'].apply(lambda x: x.replace(' ','_'))

available_species = image_metadata[['species','species_display']].drop_duplicates().to_dict('records')
#####################

available_phenophase = [{'phenophase':'371',
                         'phenophase_display':'Leaves'},
                        {'phenophase':'501',
                         'phenophase_display':'Flowers'}]

############
available_images = image_metadata.img_filename.tolist()
##############################
##############################

json_metadata = {'available_issue_dates':available_issue_dates,
                 'available_species':available_species,
                 'available_phenopahse':available_phenophase,
                 'available_images':available_images}

with open('html/image_metadata.json','w') as f:
    json.dump(json_metadata, f, indent=4)

