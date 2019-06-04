import datetime
import os
import urllib
import time
import yaml
import json
import numpy as np
import pandas as pd

from fabric import Connection

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
        request.close()
        return True
    except:
        return False

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
        hostname = os.uname().nodename
        
        # Check if we're on a hipergator node,
        # which can have many different prefixes.
        if 'ufhpc' in hostname:
            hostname = 'ufhpc'
        
        try:
            data_folder = config['data_folder'][hostname]
        except KeyError:
            data_folder = config['data_folder']['default']

    config['data_folder'] = data_folder
    
    make_folder(data_folder)

    for key, value in config.items():
        is_file = 'file' in key
        is_folder = 'folder' in key
        if (is_file or is_folder) and key != 'data_folder':
            config[key] = data_folder + value
        if (is_folder):
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

# This appends csv's while keeping the header intact
# or creates a new file if it doesn't already exist.
def append_csv(df, filename):
    old_data = pd.read_csv(filename)
    all_old_columns_in_new = old_data.columns.isin(df.columns).all()
    all_new_columns_in_old = df.columns.isin(old_data.columns).all()
    if not all_old_columns_in_new or not all_new_columns_in_old:
        raise RuntimeError('New dataframe columns do not match old dataframe')
    
    appended = old_data.append(df)
    appended.to_csv(filename, index=False)

# Re-write a csv with updated info
def update_csv(df, filename):
    os.remove(filename)
    df.to_csv(filename, index=False)

def aic(obs, pred, n_param):
    assert isinstance(obs, np.ndarray) and isinstance(pred, np.ndarray), 'obs and pred should be np arrays'
    assert obs.shape==pred.shape, 'obs and pred should have the same shape'
    
    return len(obs) * np.log(np.mean((obs - pred)**2)) + 2*(n_param + 1)

def write_json(obj, filename, overwrite=False):
    if os.path.exists(filename) and not overwrite:
        raise RuntimeWarning('File {f} exists. User overwrite=True to overwite'.format(f=filename))
    else:
        with open(filename, 'w') as f:
            json.dump(obj, f, indent=4)

def read_json(filename):
    with open(filename, 'r') as f:
        m = json.load(f)
    return m


class RemoteRunControl():
    def __init__(self, con_info, remote_status_filename,
                 connection_attempts=10, wait_time=60*5):        
        self.con_info = con_info
        self.remote_status_filename = remote_status_filename        
        self.connection_attempts = connection_attempts
        self.wait_time = wait_time
        
        assert connection_attempts>0

    def _remote_command(self, command, attempt=1): 
        if attempt==self.connection_attempts:
            print('Cannot connect to server')
            raise
        else:
            try:
                with Connection(**self.con_info, connect_kwargs={'banner_timeout':120}) as c:
                    command_output = c.run(command, warn=True)
                return command_output
            except:
                print('command run failed: "{c}" \n' \
                      'attempt: {x}/{y}'.format(c=command, x=attempt,y=self.connection_attempts))
                time.sleep(self.wait_time)
                return self._remote_command(attempt=attempt+1, command=command)
    
    def remote_run_complete(self):
        # If the status file is present then the run is complete. 
        # an error is returned (and ls_output==false) if the file is not present
        ls_output = self._remote_command('ls ' + self.remote_status_filename)
           
        return ls_output.ok
    
    def submit_job(self, remote_job_script):
        sbatch_output = self._remote_command('sbatch ' + remote_job_script)
    
    def get_file(self, remote_path, local_path):
        transfer_succesful = True
        with Connection(**self.con_info) as c:
            try:
                c.get(remote = remote_path, local = local_path)
            except:
                raise RuntimeWarning('could  not transfer file: ' + remote_path)
                transfer_succesful = False
        
        return transfer_succesful
            
            
    def remote_run_info(self):
        # Get the remote status file as a dictionary.
        cat_output = self._remote_command('cat ' + self.remote_status_filename)
            
        if cat_output.ok:
            return json.loads(cat_output.stdout)
        else:
            raise RuntimeError('cannot read remote status file')
    
    def clear_status_file(self):
        rm_output = self._remote_command('rm ' + self.remote_status_filename)
