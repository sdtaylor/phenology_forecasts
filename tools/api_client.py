import requests as r
import yaml
import pandas as pd

class PhenologyForecastAPIClient():
    def __init__(self, credential_file=None, 
                 hostname='https://phenology.naturecast.org/api/'):
        self.logged_in=False
        self.headers={}
        self.hostname = hostname
        self.credential_file=credential_file
    
    def _make_request(self, http_method, url, data=None):
        request = http_method(self.hostname + url, 
                              headers = self.headers,
                              data = data)
        if not request.ok:
            try:
                error = request.json()
            except:
                error = ''
            raise RuntimeError('request failed for: '+url,
                               error)
        
        return request.json()
    
    def _load_credential_file(self):
        with open(self.credential_file, 'r') as f:
            credentials = yaml.load(f)
        
        if 'username' not in credentials or 'password' not in credentials:
            raise RuntimeError('Credential file reques "username" and',
                               '"password" fields')
        
        return {'username': credentials['username'], 'password':credentials['password']}
        
    def login(self, username=None, password=None):
        if username is None and password is None:
            if self.credential_file is None:
                raise RuntimeError('no credientials provided')
            else:
                credentials = self._load_credential_file()
        else:
            credentials = {'username':username, 'password':password}
        
        token_request = r.post('https://phenology.naturecast.org/accounts/api/api-token-auth/', 
                              data=credentials)
        if token_request.ok:
            token = token_request.json()['token']
            self.logged_in=True
            self.headers['Authorization'] = 'Token '+format(token)
            
            self._load_current_entries()
    
    def _get_species_pk(self, species):
        entry = self.current_species.query('species == @species')
        if entry.empty:
            raise RuntimeError('species not found: '+species)
        else:
            return entry.id.values[0]
    
    def _get_phenophase_pk(self, phenophase):
        entry = self.current_phenophases.query('phenophase == @phenophase')
        if entry.empty:
            raise RuntimeError('phenophase not found: '+phenophase)
        else:
            return entry.id.values[0]
    
    def _get_issue_date_pk(self, issue_date):
        entry = self.current_issue_dates.query('issue_date == @issue_date')
        if entry.empty:
            raise RuntimeError('issue_date not found: '+issue_date)
        else:
            return entry.id.values[0]
    
    def _load_current_entries(self):
        self.current_issue_dates = pd.DataFrame(self.issue_date_list())
        self.current_species = pd.DataFrame(self.species_list())
        self.current_forecasts = pd.DataFrame(self.forecast_list())
        self.current_phenophases = pd.DataFrame(self.phenophases_list())
    
    def logout(self):
        pass
    
    def species_list(self):
        endpoint = 'species/list/'
        return self._make_request(r.get, endpoint)
    
    def species_create(self, species_info):
        endpoint = 'species/create/'
        return self._make_request(r.post, endpoint, data=species_info)
    
    def species_update(self, species_info):
        endpoint = 'species/update/' + species_info['species'] + '/'
        self._make_request(r.put, endpoint, data=species_info)
        
    def species_detail(self, species_info):
        endpoint = 'species/update/' + species_info['species'] + '/'
        self._make_request(r.get, endpoint, data=species_info)
    
    def phenophases_list(self):
        endpoint = 'phenophases/list/'
        return self._make_request(r.get, endpoint)
    
    def issue_date_list(self):
        endpoint = 'issuedates/list/'
        return self._make_request(r.get, endpoint)
    
    def issue_date_create(self, issue_date_info):
        endpoint = 'issuedates/create/'
        return self._make_request(r.post, endpoint, data=issue_date_info)
    
    def issue_date_update(self, issue_date_info):
        endpoint = 'issuedates/update/' + issue_date_info['issue_date'] + '/'
        return self._make_request(r.put, endpoint, data=issue_date_info)
    
    def forecast_list(self):
        """
        Get a list of dictionaries with all the current forecasts. See 
        forecast_create for an example dictionary. 
        """
        endpoint = 'forecasts/list/'
        return self._make_request(r.get, endpoint)
    
    def forecast_create(self, forecast_info):
        """"
        Authentication required
        
        Create a new forecast with the following like the following
        
        {
        "issue_date": "2018-12-03",
        "species": "acer_rubrum",
        "phenophase": 371,
        "prediciton_image_filename": "acer_rubrum_371_2018-12-03_prediction.png",
        "uncertainty_image_filename": "acer_rubrum_371_2018-12-03_uncertainty.png",
        "anomaly_image_filename": "acer_rubrum_371_2018-12-03_anomaly.png",
        }
        """
        endpoint = 'forecasts/create/'
        return self._make_request(r.post, endpoint, data=forecast_info)