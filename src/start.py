import os

from uvicorn import run
from uvicorn import run
from app import create_app

app = create_app()

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    run(app=app, host='0.0.0.0', port=int(server_port))

