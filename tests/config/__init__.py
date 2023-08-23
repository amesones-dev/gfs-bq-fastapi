# Google BigQuery service account key json file
import os


class TestConfig(object):
    settings = ['BQ_SA_KEY_JSON_FILE', 'API_NAME', 'API_VER', 'VIEW_APP_NAME']
    BQ_SA_KEY_JSON_FILE = os.environ.get('TEST_BQ_SA_KEY_JSON_FILE') or '/etc/secrets/sa_key_bq_tests.json'
    API_NAME = os.environ.get('TEST_API_NAME') or 'fastapi_demo_test'
    API_VER = os.environ.get('TEST_API_VER') or 'alpha'
    VIEW_APP_NAME = os.environ.get('TEST_VIEW_APP_NAME') or 'fastapi_demo_app_test'

    def to_dict(self):
        r = {}
        for k in self.settings:
            r[k] = self.__getattribute__(k)
        return r

