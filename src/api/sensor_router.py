from fastapi import APIRouter
from src.services.sensor_service import SensorService

class SensorRouter:
    def __init__(self):
        self.sensor_data_service = SensorService()
        self.router = APIRouter(prefix="/sensor")
        self.register_routes()

    def register_routes(self):
        self.router.post("/")(self.sensor_data_service.insertSensorData)
        self.router.get("/{gml_id}")(self.sensor_data_service.getByGmlId)

    def get_router(self):
        return self.router
