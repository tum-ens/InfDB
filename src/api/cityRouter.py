from fastapi import APIRouter
from src.services.citydb_service import CityDBService

class CityRouter:
    def __init__(self):
        self.city_db_service = CityDBService()
        self.router = APIRouter(prefix="/city")
        self.register_routes()

    def register_routes(self):
        self.router.post("/")(self.city_db_service.insertCityObject)

    def get_router(self):
        return self.router
