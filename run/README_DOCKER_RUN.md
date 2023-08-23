## Local environment build of a specific feature branch
* Repo:  [gfs-bq-fastapi](https://github.com/amesones-dev/gfs-bq-fastapi.git) 
* Branch to build: [main](https://github.com/amesones-dev/gfs-bq-fastapi/tree/main)
* [Dockerfile](https://github.com/amesones-dev/gfs-bq-fastapi/blob/main/run/Dockerfile)  
* Running the application with uvicorn: [start.py](https://github.com/amesones-dev/gfs-bq-fastapi/blob/main/src/start.py)

**Dockerfile**
```Dockerfile
# Python image to use.
FROM python:3.10-alpine

# Set the working directory to /app
WORKDIR /app

# copy the requirements file used for dependencies
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the rest of the working directory contents into the container at /app
COPY . .

# Run app.py when the container launches
ENTRYPOINT ["python", "start.py"]
```
**Startup script run by docker image**
```python
# start.py
import os

from uvicorn import run
from uvicorn import run
from app import create_app

app = create_app()

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    run(app=app, host='0.0.0.0', port=int(server_port))

```

### Instructions
```shell
# Clone repo and checkout specific branch
REPO="https://github.com/amesones-dev/gfs-bq-fastapi.git"
TAG="gfs-bq-fastapi:v1"
git clone ${REPO}
docker build ./gfs-bq-fastapi/src/ -f ./gfs-bq-fastapi/run/Dockerfile - t ${TAG}

# Default container port is 8080 if PORT not specified
export PORT=8081


# Minimum config for BigQuery SA key
# Option 1
# Implicit app authentication to Cloud BigQuery API 
# Use GOOGLE_APP_CREDENTIALS variable if set in environment or Default Cloud running service SA
# export BQ_SA_KEY_JSON_FILE=""

# Option 2
# Explict app authentication
# If variable not defined in environment it defaults to '/etc/secrets/sa_key_bq.json'
# 
# export BQ_SA_KEY_JSON_FILE='/path_to/sa_bq_key.json'



# Alternatively mount local path with SA key to /etc/secrets
export SA_KEY_PATH='/local_path_to_SA_key_file_folder'
ls ${SA_KEY_PATH}
# Output
    sa_key_bq.json

export BQ_SA_KEY_JSON_FILE='/etc/secrets/sa_key_bq.json'

# Mount local path to /etc/secrets when running container
docker run -p ${PORT}:${PORT} -e PORT=${PORT} -e BQ_SA_KEY_JSON_FILE="${BQ_SA_KEY_JSON_FILE}" -v "${SA_KEY_PATH}":/etc/secrets  ${TAG}

```
