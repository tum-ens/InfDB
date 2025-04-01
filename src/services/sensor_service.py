from fastapi import HTTPException
from src.db.models import SensorReading
from src.schemas.sensor_data import SensorData
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

    # def insertSensorData(self, data: SensorData):
    #     try:
    #         with Session(timescale_engine) as session:
    #             sensor_reading = SensorReading(
    #                 timestamp=data.timestamp,
    #                 gml_id=data.gml_id,
    #                 sensor_name=data.sensor_name,
    #                 value=data.value
    #             )
    #             session.add(sensor_reading)
    #             session.commit()
    #             session.refresh(sensor_reading)  # Refresh to get the new ID

    #         return sensor_reading.id
    #     except Exception as e:
    #         raise HTTPException(status_code=500, detail=f"Database insertion failed: {str(e)}")

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
                    if (hasattr(SensorReading, key)):
                        statement = statement.where(getattr(SensorReading, key) == value)

                sensor_readings = session.exec(statement).all()
                return sensor_readings

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
