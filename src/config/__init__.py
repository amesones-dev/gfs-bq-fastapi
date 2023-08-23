# Google BigQuery service account key json file
import os


class Config(object):
    settings = ['BQ_SA_KEY_JSON_FILE', 'API_NAME', 'API_VER', 'VIEW_APP_NAME']
    BQ_SA_KEY_JSON_FILE = os.environ.get('BQ_SA_KEY_JSON_FILE') or '/etc/secrets/sa_key_bq.json'
    API_NAME = os.environ.get('API_NAME') or 'gfs-bq-fastapi'
    API_VER = os.environ.get('API_VER') or 'alpha'
    VIEW_APP_NAME = os.environ.get('VIEW_APP_NAME') or 'fastapi_demo_app'

    def to_dict(self):
        r = {}
        for k in self.settings:
            r[k] = self.__getattribute__(k)
        return r

