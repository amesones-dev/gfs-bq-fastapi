from fastapi.encoders import jsonable_encoder


def status_ok():
    payload = {"status": "OK"}
    return jsonable_encoder(payload)


def app_home(current_app):
    payload = {"name": current_app.config.get('API_NAME'), "ver": current_app.config.get('API_VER')}
    return jsonable_encoder(payload)
