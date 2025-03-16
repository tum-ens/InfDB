from src.externals.weatherApi import WeatherAPI


class WeatherService:
    def __init__(self):
        self.api = WeatherAPI()

    def getHistoricalData(self):
        params = {
            "latitude": 52.52,
            "longitude": 13.41,
            "start_date": "2025-02-28",
            "end_date": "2025-03-14",
            "hourly": "temperature_2m"
        }
        # Get weather data
        weather_data = self.api.get_weather_data(params)

        return weather_data
