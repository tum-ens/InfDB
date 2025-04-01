from fastapi import Query, status
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from src.services.weather_service import WeatherService

router = InferringRouter(prefix="/weather")
sensor_service = WeatherService()


@cbv(router)
class WeatherRouter:
    @router.get("/")
    async def get(self, resolution: int = Query):
        sensor_service.getHistoricalData(resolution)

