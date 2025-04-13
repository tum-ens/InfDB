from typing import Optional
from fastapi import Query
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from src.exceptions.weatherException import InvalidWeatherParameterError
from src.services.weather_service import WeatherService

from pydantic import BaseModel
from datetime import date, datetime


class DateRange(BaseModel):
    startDate: date
    endDate: date


router = InferringRouter(prefix="/weather")


@cbv(router)
class WeatherRouter:
    weatherService = WeatherService()

    @router.post("/weather-data/{resolution}", tags=["Weather Data"])
    async def postWeatherData(self, resolution: int, dateRange: DateRange, sensorNames: list[str]):
        try:
            self.weatherService.insertHistoricalData(resolution, dateRange.startDate, dateRange.endDate, sensorNames)
            return {"message": "Data processed"}
        except InvalidWeatherParameterError as e:
            return {
                "error": str(e),
                "details": e.details
            }

    @router.get("/weather-data/{resolution}", tags=["Weather Data"])
    async def getBuildingData(
        self,
        resolution: int,
        buildingId: Optional[str] = Query(None),
        startTime: Optional[datetime] = Query(None),
        endTime: Optional[datetime] = Query(None)
    ):
        return self.weatherService.getData(resolution, buildingId, startTime, endTime)
