import json
from fastapi import HTTPException
from src.db.models.weatherReading import WeatherReading
from src.db.repositories.weatherRepository import WeatherRepository
from src.externals.weatherApi import WeatherAPI
from datetime import date, datetime
from src.services.citydb_service import CityDBService


class WeatherService:
    def __init__(self):
        self.api = WeatherAPI()
        self.cityDbService = CityDBService()
        self.repository = WeatherRepository()

    def insertHistoricalData(self, resolution: int, start_date: date, end_date: date, sensorNames: list[str]):
        centers = self.cityDbService.getRasterCenters(resolution)

        for center in centers:
            params = {
                "latitude": center.latitude,
                "longitude": center.longitude,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "hourly": sensorNames
            }

            weather_data = json.loads(self.api.getHourlyWeatherData(params))
            for entry in weather_data:
                readings = []
                for sensor in sensorNames:
                    reading = WeatherReading(
                        raster_id=str(center.rasterid),
                        timestamp=datetime.strptime(entry["date"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                        sensor_name=sensor,
                        value=entry[sensor],
                    )
                    readings.append(reading)

                self.repository.insertSensorData(readings)

    def getData(self, resolution: int, building_id: str, start: datetime | None, end: datetime | None):
        center = self.cityDbService.getRasterCenter(building_id, resolution)
        if not center:
            raise HTTPException(status_code=404, detail="Raster center not found")

        raster_id = str(center["raster_id"])
        filters = {"raster_id": raster_id}

        if start is not None:
            filters["timestamp__gte"] = start
        if end is not None:
            filters["timestamp__lte"] = end

        return self.repository.get(filters)
