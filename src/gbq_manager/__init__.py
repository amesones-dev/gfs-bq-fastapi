from google.cloud import bigquery
import os
import logging


class GBQManager:

    def __init__(self):
        self.client = None
        self.app = None

    # Link BigQueryManager to validated app
    def init_app(self, app):
        if self.validate_app(app):
            sa_creds_json_file = app.config['BQ_SA_KEY_JSON_FILE']
            if sa_creds_json_file == "":
                # Use default Google Cloud application credentials or running Cloud service identity
                try:
                    self.client = bigquery.Client()
                except Exception as e:
                    logging.log(level=logging.ERROR,
                                msg="Exception {}:{} Method: {}".format(e.__class__, e, self.init_app.__name__))
                    pass
            else:
                # Credential from file
                try:
                    self.client = bigquery.Client.from_service_account_json(sa_creds_json_file)
                except Exception as e:
                    logging.log(level=logging.ERROR,
                                msg="Exception {}:{} Method: {}".format(e.__class__, e, self.init_app.__name__))
                    pass
            if self.initialized():
                self.app = app

    # Checks a valid bigquery client is stored in attribute client
    def initialized(self) -> bool:
        return self.client is not None \
               and isinstance(self.client, bigquery.Client)

    def close_connection(self):
        if self.initialized():
            self.client.close()

    # Validates whether an app can be integrated with gbq_manager
    @staticmethod
    def validate_app(app) -> bool:
        # App: any object that has a 'config' property which is a dictionary
        # Example: could be a Flask app, a FastAPI app, etc.
        # For the app to use the BigQueryManager, the dictionary must contain the following key values.
        # app.config['FSM_SA_KEY_JSON_FILE']: path to Google Cloud Project Service Account credentials file.

        # Option 1. Valid path to existent  Google Cloud service account key json file
        # FROM OS or known filesystem path
        # BQ_SA_KEY_JSON_FILE = os.environ.get('BQ_SA_KEY_JSON_FILE') or '/etc/secrets/sa_key_bq.json'

        # Option 2. Empty string to use Google Cloud Application credentials environment
        # Default Google Cloud Application credentials
        # BQ_SA_KEY_JSON_FILE = ''

        validation = False
        required = ['BQ_SA_KEY_JSON_FILE']
        if 'config' in app.__dict__:
            if isinstance(app.config, dict):
                # Check mandatory config keys exist
                if set(required).issubset(app.config.keys()):
                    validation = app.config['BQ_SA_KEY_JSON_FILE'] == "" \
                                 or (app.config['BQ_SA_KEY_JSON_FILE'] != ""
                                     and os.path.isfile(app.config['BQ_SA_KEY_JSON_FILE']))
        return validation
