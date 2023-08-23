from fastapi.encoders import jsonable_encoder
from gbq_content_manager import AppBQContentManager

# Singleton
# Includes the app configuration set in app factory
bq_cm = AppBQContentManager()


def get_countries():
    key = get_countries.__name__
    payload = bq_cm.load_content(key=key)
    return jsonable_encoder(payload)


def get_country_evolution(country: str):
    # Total cases confirmed for latest date published for  country
    # List of territories for country
    key = get_country_evolution.__name__
    payload = bq_cm.load_content(key=key, country=country)
    return jsonable_encoder(payload)