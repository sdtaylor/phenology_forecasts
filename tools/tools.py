import datetime

def string_to_date(s, hour=False):
    if hour:
        return datetime.datetime.strptime(s, '%Y%m%d%H')
    else:
        return datetime.datetime.strptime(s, '%Y%m%d')
    
def cleanup_tmp_folder():
    for f in os.listdir(config['tmp_folder']):
        os.remove(config['tmp_folder']+f)