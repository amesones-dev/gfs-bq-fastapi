from fastapi import APIRouter
from app.routers.route_handlers import get_countries as countries
from app.routers.route_handlers import get_country_evolution as country_evolution

router = APIRouter()


@router.get("/countries/", tags=["countries"])
def get_countries():
    return countries()


@router.get("/countries/{country}/evolution/", tags=["countries"])
def get_countries_evolution(country: str):
    return country_evolution(country)
