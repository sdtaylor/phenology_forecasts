import datetime
import os
import urllib
import time

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
                return -1
            else:
                time.sleep(30)
                continue
        break

def cleanup_tmp_folder(folder):
    for f in os.listdir(folder):
        os.remove(folder+f)
