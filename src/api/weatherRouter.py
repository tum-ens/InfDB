from typing import Optional
from fastapi import Query, status
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from src.services.weather_service import WeatherService


from pydantic import BaseModel
from datetime import date, datetime

class DateRange(BaseModel):
    start_date: date
    end_date: date

router = InferringRouter(prefix="/weather")
sensor_service = WeatherService()

@cbv(router)
class WeatherRouter:
    @router.post("/weather-data/{resolution}", tags=["Weather Data"])
    async def post_weather_data(self, resolution: int, date_range: DateRange):
        sensor_service.insertHistoricalData(resolution, date_range.start_date, date_range.end_date)
        return {"message": "Data processed"}


    @router.get("/weather-data/{resolution}", tags=["Weather Data"])
    async def get_building_data(
        self,
        resolution: int,
        building_id: Optional[str] = Query(None),
        start_time: Optional[datetime] = Query(None),
        end_time: Optional[datetime] = Query(None)
    ):
        return sensor_service.get_weather_data(resolution, building_id, start_time, end_time)
