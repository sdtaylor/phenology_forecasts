import os
import glob
from google.cloud import storage
#from google.oauth2 import service_account
from tools import tools

# Sync static  images and image metadata to the website on google cloud storage

def run(update_all_images=False, metadata_only=False):
    config = tools.load_config()
    
    # Setup authentation to google cloud
    if config['google_auth'] == None:
        raise RuntimeError('google authentation file not set')
        
    os.environ['GOOGLE_APPLICATION_CREDENTIALS']=config['google_auth']
    
    client = storage.Client()
    phenology_bucket = client.bucket('phenology.naturecast.org')
    
    # Iteration thru all the images and upload if they are not already there
    issue_date_folders = glob.glob(config['phenology_forecast_figure_folder']+'2*')
    
    if not metadata_only:
        for f in issue_date_folders:
            issue_date = os.path.basename(f)
            available_images = glob.glob(f+'/*.png')
            
            for image_path in available_images:
                image_filename = os.path.basename(image_path)
                storage_path = 'images/{issue_date}/{filename}'.format(issue_date=issue_date,
                                                                       filename=image_filename)
                
                image_blob = phenology_bucket.blob(storage_path)
                if image_blob.exists() and not update_all_images:
                    pass
                    #print('{i} exists, moving on'.format(i=image_filename))
                else:
                    print('uploading {i}'.format(i=image_filename))
                    image_blob.upload_from_filename(image_path)
                    image_blob.make_public()
    
    # Update the image metadata file
    metadata_blob=phenology_bucket.blob('image_metadata.json')
    metadata_blob.upload_from_filename(config['phenology_forecast_figure_folder']+'image_metadata.json')
    metadata_blob.make_public()

if __name__=='__main__':
    run()
