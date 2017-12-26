import datetime
import os
import urllib
import time
import yaml

def string_to_date(s, h=False):
    assert isinstance(s, str) ,'date not a string'
    if h:
        assert len(s)==10, 'string with hour wrong length: '+s
        return datetime.datetime.strptime(s, '%Y%m%d%H')
    else:
        assert len(s)==8, 'string without hour wrong length: '+s
        return datetime.datetime.strptime(s, '%Y%m%d')

def date_to_string(d, h=False):
    assert isinstance(d, datetime.datetime), 'date note a datetime'
    if h:
        return d.strftime('%Y%m%d%H')
    else:
        return d.strftime('%Y%m%d')

def download_file(download_path, dest_path, num_attempts=2):
    for attempt in range(1,num_attempts+1):
        try:
            urllib.request.urlretrieve(download_path, dest_path)
        except:
            if attempt==num_attempts:
                return 1
            else:
                time.sleep(30)
                continue
        return 0

def file_available(path):
    try:
        request = urllib.request.urlopen(path)
    except urllib.error.HTTPError:
        return False
    
    return request.code==200

def cleanup_tmp_folder(folder):
    for f in os.listdir(folder):
        os.remove(folder+f)

def make_folder(f):
    if not os.path.exists(f):
        os.makedirs(f)

def load_config(data_folder=None):
    with open('config.yaml', 'r') as f:
        config = yaml.load(f)

    if data_folder is None:
        data_folder = config['data_folder']

    make_folder(data_folder)

    for key, value in config.items():
        if ('file' in key or 'folder' in key) and key != 'data_folder':
            config[key] = data_folder + value
            make_folder(config[key])
    
    return config

def current_growing_season(config):
    today = datetime.datetime.today()
    year = today.strftime('%Y')
    season_begin = year+config['season_month_begin']+config['season_day_begin']
    cutoff = datetime.datetime.strptime(season_begin, '%Y%m%d')
    if today >  cutoff:
        year = str(int(year) + 1)
    return year