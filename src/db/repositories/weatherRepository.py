from fastapi import HTTPException
from src.db.models import WeatherReading
from sqlmodel import Session, select
from src.core.config_db import timescale_engine


class WeatherRepository:
    def insertSensorData(self, readings: list[WeatherReading]):
        try:
            with Session(timescale_engine) as session:
                session.add_all(readings)
                session.commit()
            return
        except Exception as e:
            print(f"Database insertion failed: {e}")
            return None

    def get(self, filters: dict[str, any]):
        try:
            with Session(timescale_engine) as session:
                statement = select(WeatherReading)

                for key, value in filters.items():
                    # is this correct place to check for filter params or api level is better?
                    if key == "timestamp__gte":
                        statement = statement.where(WeatherReading.timestamp >= value)
                    elif key == "timestamp__lte":
                        statement = statement.where(WeatherReading.timestamp <= value)
                    elif (hasattr(WeatherReading, key)):
                        statement = statement.where(getattr(WeatherReading, key) == value)

                sensor_readings = session.exec(statement).all()
                return sensor_readings

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
