import json

from fastapi import HTTPException
from src.db.models.sensor_reading import SensorReading
from src.externals.weatherApi import WeatherAPI
from datetime import date, datetime, timedelta
from src.services.citydb_service import CityDBService
from src.services.sensor_service import SensorService
from sqlmodel import Session, select

class WeatherService:
    def __init__(self):
        self.api = WeatherAPI()
        self.cityDbService = CityDBService()
        self.sensorService = SensorService()

    def insertHistoricalData(self, resolution: int, start_date: date, end_date: date):
        centers = self.cityDbService.getGridCenters(resolution)

        for center in centers:
            params = {
                "latitude": center.latitude,
                "longitude": center.longitude,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "daily": "temperature_2m_max"
            }

            weather_data = json.loads(self.api.get_weather_data(params))

            readings = []
            for entry in weather_data:
                reading = SensorReading(
                    raster_id=str(center.rasterid),
                    timestamp=datetime.strptime(entry["date"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                    sensor_name="temperature_2m_max",
                    value=entry["temperature_2m"],
                )
                self.sensorService.insertSensorData(reading)
                readings.append(reading)

    def get_weather_data(self, resolution: int, building_id: str, start: datetime | None, end: datetime | None):
        center = self.cityDbService.getGridCenter(building_id, resolution)
        if not center:
            raise HTTPException(status_code=404, detail="Grid center not found")

        raster_id = str(center["grid_id"])
        filters = {"raster_id": raster_id}

        if start is not None:
            filters["timestamp__gte"] = start
        if end is not None:
            filters["timestamp__lte"] = end

        return self.sensorService.get(filters)

