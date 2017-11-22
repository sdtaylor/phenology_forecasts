import datetime
import os

def string_to_date(s, h=False):
    assert isinstance(s, str) ,'date not a string'
    if h:
        assert len(s)==10, 'string with hour too short: '+s
        return datetime.datetime.strptime(s, '%Y%m%d%H')
    else:
        assert len(s)==8, 'string without hour too short: '+s
        return datetime.datetime.strptime(s, '%Y%m%d')

def date_to_string(d, h=False):
    assert isinstance(d, datetime.datetime), 'date note a datetime'
    if h:
        return d.strftime('%Y%m%d%H')
    else:
        return d.strftime('%Y%m%d')


def cleanup_tmp_folder():
    for f in os.listdir(config['tmp_folder']):
        os.remove(config['tmp_folder']+f)