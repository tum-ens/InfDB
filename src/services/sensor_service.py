from fastapi import HTTPException
from src.db.models import SensorReading
from sqlmodel import Session, select
from src.core.db_config import timescale_engine


class SensorService:
    def insertSensorData(self, reading: SensorReading):
        try:
            with Session(timescale_engine) as session:
                session.add(reading)
                session.commit()
                session.refresh(reading)
            return reading.id
        except Exception as e:
            print(f"Database insertion failed: {e}")
            return None

    def getByGmlId(self, gml_id: str):
        try:
            with Session(timescale_engine) as session:
                statement = select(SensorReading).where(SensorReading.gml_id == gml_id)
                sensor_readings = session.exec(statement).all()
                return sensor_readings
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

    def get(self, filters: dict[str, any]):
        try:
            with Session(timescale_engine) as session:
                statement = select(SensorReading)

                for key, value in filters.items():
                    # is this correct place to check for filter params or api level is better?
                    if key == "timestamp__gte":
                        statement = statement.where(SensorReading.timestamp >= value)
                    elif key == "timestamp__lte":
                        statement = statement.where(SensorReading.timestamp <= value)
                    elif (hasattr(SensorReading, key)):
                        statement = statement.where(getattr(SensorReading, key) == value)

                sensor_readings = session.exec(statement).all()
                return sensor_readings

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
