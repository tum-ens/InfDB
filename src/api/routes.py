from fastapi import APIRouter
from .sensorRouter import SensorRouter
from .cityRouter import CityRouter


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
