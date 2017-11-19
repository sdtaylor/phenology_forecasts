# Create the north american land mask from a prism file
import yaml
import numpy as np
import prism_utils

with open('config.yaml', 'r') as f:
    config = yaml.load(f)
    
mask_filename = config['data_folder'] + config['mask_file']

prism = prism_utils.prism_ftp_info()

prism_date = prism_utils.string_to_date('20100101')

prism_array = prism_utils.download_and_process_day(prism, prism_date,
                                       varname='tmean',status='stable')
prism_array = prism_array.drop('time')
land_values = ~np.isnan(prism_array.tmean.values)
prism_array['land'] = (('lat','lon'), land_values[0])
prism_array = prism_array.drop(['tmean','status'])

prism_array.to_netcdf(mask_filename)

