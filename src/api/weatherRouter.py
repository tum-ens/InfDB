from fastapi import HTTPException, Query
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from src.services.weather_service import WeatherService

router = InferringRouter(prefix="/weather")
sensor_service = WeatherService()


@cbv(router)
class WeatherRouter:
    @router.get("/")
    async def get(self, resolution: int = Query):
        result = sensor_service.getHistoricalData(resolution)
        if not result:
            raise HTTPException(status_code=404, detail="No sensor data found")
        return result
