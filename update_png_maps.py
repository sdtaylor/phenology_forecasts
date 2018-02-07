from tools import tools
import os
import glob
import subprocess

# This rewrites all static map images using all the available
# netcdf files in phenology_forecasts/phenology_forecasts
#
# It's for when I do some update on the static maps and want to
# redo all maps from prior issue dates


config = tools.load_config()


available_forecasts = glob.glob(config['phenology_forecast_folder']+'*.nc')

for f in available_forecasts:
    print('Making maps for: '+os.path.basename(f))
    subprocess.call(['/usr/bin/Rscript',
                     '--vanilla',
                     'automated_forecasting/presentation/build_png_maps.R',
                     f])