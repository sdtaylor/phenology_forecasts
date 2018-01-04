# Create the north american land mask from a prism file
import numpy as np
from tools import prism_tools
from tools import tools

config = tools.load_config()
    
mask_filename = config['mask_file']

prism = prism_tools.prism_ftp_info()

prism_date = tools.string_to_date('20100101')

prism_array = prism_tools.download_and_process_day(prism, prism_date,
                                       varname='tmean',status='stable')
prism_array = prism_array.drop('time')
land_values = ~np.isnan(prism_array.tmean.values)
prism_array['land'] = (('lat','lon'), land_values[0])
prism_array = prism_array.drop(['tmean','status'])

prism_array.to_netcdf(mask_filename)

