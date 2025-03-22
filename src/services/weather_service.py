from src.externals.weatherApi import WeatherAPI
from datetime import date, timedelta

from src.services.citydb_service import CityDBService


class WeatherService:
    def __init__(self):
        self.api = WeatherAPI()
        self.cityDbService = CityDBService()

    def getHistoricalData(self):
        centers = self.cityDbService.getGridCenters()
        today = date.today()
        one_year_ago = today - timedelta(days=365)

        all_weather_data = []
        for center in centers:
            params = {
                "latitude": center.latitude,
                "longitude": center.longitude,
                "start_date": one_year_ago.strftime("%Y-%m-%d"),
                "end_date": today.strftime("%Y-%m-%d"),
                "daily": "temperature_2m_max"
            }

            # Get weather data
            weather_data = self.api.get_weather_data(params)
            all_weather_data.append(weather_data)

        return all_weather_data
