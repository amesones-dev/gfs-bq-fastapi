from fastapi import FastAPI
from app.routers import countries


from gbq_manager import GBQManager
from gbq_content_manager import AppBQContentManager
from config import Config
from app.root_handlers import status_ok, app_home


def create_app(configclass=Config) -> FastAPI:
    root_app = FastAPI()
    root_app.config = configclass().to_dict()
    # Create a BigQuery connection manager and link to this app
    bq = GBQManager()
    bq.init_app(root_app)

    # Basic Big Query sourced data in memory content manager
    # Loads data from BQ using a preconfigured set
    # Basic management of content freshness
    # to avoid running BigQuery sql queries
    # Improvement: adding content cache service (redis, memcache)

    app_bq_cm = AppBQContentManager()
    app_bq_cm.init_app(root_app, bq=bq)

    # Fast API config

    @root_app.get("/")
    async def root():
        return app_home(root_app)

    @root_app.get("/healthcheck")
    async def root():
        return status_ok()

    # Example of using modular routes with router
    root_app.include_router(countries.router)

    return root_app



