# Publish BigQuery datasets using FastAPI 

## Add API content with BigQuery
A basic example of how to use [FastAPI](https://fastapi.tiangolo.com/) to publish 
[BigQuery](https://cloud.google.com/bigquery)  datasets to consumers.  
Ideally meant to publish organizational datasets to consumer teams.  
This example uses a public dataset for worldwide CV19 infections statistics  queried using 
[BigQuery public datasets](https://cloud.google.com/bigquery/public-data) to generate API content.  

**Example dataset source**
* [BigQuery public dataset](https://console.cloud.google.com/marketplace/product/johnshopkins/covid19_jhu_global_case)
* [Source: covid19_jhu_csse_eu.summary](https://ccp.jhu.edu/kap-covid)  

## GBQManager class

**GBQManager**
1. Creates a  BigQuery API client from a service account key file  
  *Note: required IAM roles for service account: BigQuery User*
2. Isolates BigQuery connections management

**Class use example to manage BigQuery connections for an app**  

*Link GBQManager to app*
```python
    # App specific
    # Link GBQManager to app
    bq = GBQManager()
    bq.init_app(self.app)
```

*Use GBQManager to run BigQuery query jobs*    
```python    
    sql_query = """SELECT DISTINCT country_region  
                FROM `bigquery-public-data.covid19_jhu_csse_eu.summary`  
                ORDER BY country_region ASC""" 
    query_job = bq.client.query(query=sql_query)
```

**App configuration keys used by GBQManager class**
```shell
   # Google Cloud Logging service account key json file
   # Determines service account and hence BigQuery project permissions
    BQ_SA_KEY_JSON_FILE = os.environ.get('BQ_SA_KEY_JSON_FILE') or '/etc/secrets/sa_key_bq.json'
 ```

## AppBQContentManager class
**AppBQContentManager**  

Basic content manager that isolates content metadata management and provides basic content cache.
1. Maintains a list of contents, content titles and SQL queries definitions used to generate them.
2. Uses a GBQManager to manage BigQuery connections.
 
**Class use example to publish BigQuery data**  

*Link BigQueryManager to app*
```python
    # Basic Big Query sourced data in memory content manager
    # Loads data from BQ using a preconfigured set of titles and SQL queries
    # Basic management of content freshness to avoid duplicated running BigQuery sql queries
    # Possible improvement: adding content cache service (redis, memcache)
    
    from gbq_manager import GBQManager
    from fastapi.encoders import jsonable_encoder
    ...

    app_bq_cm = AppBQContentManager()
    app_bq_cm.init_app(app=fastapi_app, bq=GBQManager())

    # key identifies uniquely a content (title, SQL query to generate content data)
    payload = app_bq_cm.load_content(key=key, country=country)
    return jsonable_encoder(payload)   
```


## Running the application locally  
### Create Google Cloud resources
1. Create a [Google Cloud](https://console.cloud.google.com/home/dashboard)  platform account if you do not already have it.
2. [Create a Google Cloud project](https://developers.google.com/workspace/guides/create-project) or use an existing one.
3. Configure application identity
   * Create a [Service Account(SA) key](https://cloud.google.com/iam/docs/keys-create-delete)
   * Assign the IAM role BigQuery User to the SA during creation.
 

### Use Google Cloud Shell
To start coding right away, launch [Google Cloud Shell](https://console.cloud.google.com/home/).  

### Or use your own development environment
If you would rather use *your own local development machine* you will need to  [Install Google Cloud SDK](https://cloud.google.com/sdk/docs/quickstart) and Install Python

* Install python packages.

    ```shell
    sudo apt update
    sudo apt install python3 python3-dev python3-venv
    ```
    
* Install pip 

    *Note*: Debian provides a package for pip

    ```shell
    sudo apt install python-pip
    ```
    Alternatively pip can be installed with the following method
    ```shell
    wget https://bootstrap.pypa.io/get-pip.py
    sudo python3 get-pip.py
    ```
*Note: Console snippets for Debian/Ubuntu based distributions.*
### Clone git repo from Github
At this point either you are using Cloud Shell or you have a local development environment with python and Cloud SDK.
  ```shell
  git clone https://github.com/amesones-dev/gfs-bq-fastapi.git
   ```

### Create a pyhon virtual environment

User your cloned git repository folder for your source code and Python [venv](https://docs.python.org/3/library/venv.html)
virtual environment to isolate python dependencies. 

```shell
export VENV_NAME=venv
cd gfs-bq-fastapi
python -m venv ${VENV_NAME}
source ${VENV_NAME}/bin/activate
```
Usual values for VENV_NAME are `venv`, `dvenv`, `venv39` for a python 3.9 version virtual environment, etc.

### Install python requirements
```shell
# From gfs-bq-fastapi folder
pip install -r src/requirements.txt
```


### App configuration
At this point you are ready to configure and run the application.
  * Edit the application configuration Config class to update the key BQ_SA_KEY_JSON_FILE with the SA key file path 
  created in  [Create Google Cloud resources](#create-google-cloud-resources)
  * Or set the env variable BQ_SA_KEY_JSON_FILE to point to SA key location or empty string to use default application
  credentials 
   
```shell
export BQ_SA_KEY_JSON_FILE='/etc/secrets/sa_key_bq.json'
```

### Running the FastAPI app
  * Run with python start file
  ```shell
  export PORT=8080
  python src/start.py
   ```
#

  * Run with uvicorn
   ```shell
  cd src
  export PORT=8080
  uvicorn start:app --port $PORT 
   ```
### Inspect API definition
At this point your API is published and the endpoints ready to receive requests.  
* Check the /docs endpoint to see the API definition 
* or /openapi.json to get the OpenAPI json file for your newly created API.


**Example application**
![Example application](/docs/res/img/gfsBQfastAPIdemo.png)

