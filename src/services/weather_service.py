import json
from src.db.models.sensor_reading import SensorReading
from src.externals.weatherApi import WeatherAPI
from datetime import date, datetime, timedelta
from src.services.citydb_service import CityDBService
from src.services.sensor_service import SensorService


class WeatherService:
    def __init__(self):
        self.api = WeatherAPI()
        self.cityDbService = CityDBService()
        self.sensorService = SensorService()

    def getHistoricalData(self, resolution: int):
        centers = self.cityDbService.getGridCenters(resolution)
        today = date.today()
        one_year_ago = today - timedelta(days=365)

        for center in centers:
            params = {
                "latitude": center.latitude,
                "longitude": center.longitude,
                "start_date": one_year_ago.strftime("%Y-%m-%d"),
                "end_date": today.strftime("%Y-%m-%d"),
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

        return None
