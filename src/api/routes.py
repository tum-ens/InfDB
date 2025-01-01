from fastapi import APIRouter
from src.api.sensor_router import SensorRouter
from src.api.city_router import CityRouter

class ApiRouter:
    def __init__(self):
        self.router = APIRouter()
        self.register_routes()

    def register_routes(self):
        # Add sub-routers
        self.router.include_router(SensorRouter().get_router())
        self.router.include_router(CityRouter().get_router())

    def get_router(self):
        return self.router