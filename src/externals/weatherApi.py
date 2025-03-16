import requests_cache
import pandas as pd
from retry_requests import retry
import openmeteo_requests


class WeatherAPI:
    def __init__(self):
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.client = openmeteo_requests.Client(session=retry_session)
        self.url = "https://historical-forecast-api.open-meteo.com/v1/forecast"

    def get_weather_data(self, params):
        try:
            response = self.client.weather_api(self.url, params=params)[0]
            hourly = response.Hourly()

            hourly_data = {"date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left"
            )}
            hourly_data["temperature_2m"] = hourly.Variables(0).ValuesAsNumpy()
            hourly_dataframe = pd.DataFrame(data=hourly_data)
            return hourly_dataframe.to_json(orient='records', date_format='iso')
        except AttributeError:
            return []
