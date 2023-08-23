import unittest
import warnings

# App specific imports
from config import TestConfig
from gbq_manager import GBQManager

# Config import


class MockFSOApp:
    def __init__(self, config_class=TestConfig):
        self.config = config_class().to_dict()


class GBQManagerModelCase(unittest.TestCase):
    def setUp(self):
        self.app = MockFSOApp(config_class=TestConfig)

        self.bq = GBQManager()

        # Test logging configuration
        warnings.filterwarnings(action="ignore", category=ResourceWarning)

    def tearDown(self):
        self.bq.close_connection()

    def test_0_validate_app(self):
        # app.config['BQ_SA_KEY_JSON_FILE']: path to Google Cloud Project Service Account credentials file.
        # Save original config
        sa_creds = self.app.config.get('BQ_SA_KEY_JSON_FILE')

        # Validate app with original configuration
        self.assertTrue(GBQManager.validate_app(self.app))

        # Modify config to trigger validation error
        self.app.config.update({'BQ_SA_KEY_JSON_FILE': '/non_existent_dir/non_existent_file'})
        self.assertFalse(GBQManager.validate_app(self.app))

        # Restore original config
        self.app.config.update({'BQ_SA_KEY_JSON_FILE': sa_creds})
        self.assertTrue(GBQManager.validate_app(self.app))

    def test_1_bq_default(self):
        self.assertIsNone(self.bq.client)
        self.assertIsNone(self.bq.app)

    def test_2_init_app(self):
        self.assertTrue(GBQManager.validate_app(self.app))
        # Init app
        self.bq.init_app(self.app)
        self.assertIsNotNone(self.bq.client)
        self.assertIsNotNone(self.bq.app)
        self.assertTrue(self.bq.initialized())


if __name__ == '__main__':
    unittest.main(verbosity=2)