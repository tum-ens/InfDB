import requests_cache
import pandas as pd
from retry_requests import retry
import openmeteo_requests
from src.exceptions.weatherException import InvalidWeatherParameterError


class WeatherAPI:
    def __init__(self):
        cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.client = openmeteo_requests.Client(session=retry_session)
        self.url = "https://historical-forecast-api.open-meteo.com/v1/forecast"

    # a good idea would be working in batches that would speed up everything in this part
    def getHourlyWeatherData(self, params):
        try:
            response = self.client.weather_api(self.url, params=params)[0]
            hourly = response.Hourly()

            hourly_data = {
                "date": pd.date_range(
                    start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                    end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                    freq=pd.Timedelta(seconds=hourly.Interval()),
                    inclusive="left",
                )
            }

            for i, name in enumerate(params["hourly"]):
                hourly_data[name] = hourly.Variables(i).ValuesAsNumpy()

            hourly_dataframe = pd.DataFrame(data=hourly_data)
            return hourly_dataframe.to_json(orient="records", date_format="iso")

        except Exception as e:
            error_str = str(e)

            if (
                "Data corrupted at path" in error_str
                and "invalid String value" in error_str
            ):
                raise InvalidWeatherParameterError(
                    "Invalid weather variable requested. Please check the input parameters.",
                    details=error_str,
                )

            return []
