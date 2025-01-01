from fastapi import HTTPException
from src.db.models import SensorReading
from src.schemas.sensor_data import SensorData
from sqlmodel import Session
from src.core.db_config import timescale_engine

class SensorService:
    def insertSensorData(self, data: SensorData):
        """
        Inserts sensor data into the database.

        Args:
            data (SensorData): Validated input schema for sensor data.

        Returns:
            dict: Success message and the inserted sensor reading ID.
        """
        try:
            with Session(timescale_engine) as session:
                # Create a new SensorReading record
                sensor_reading = SensorReading(
                    timestamp=data.timestamp,
                    sensor_id=data.sensor_id,
                    value=data.value
                )
                session.add(sensor_reading)  # Add to the database session
                session.commit()  # Commit the transaction
                session.refresh(sensor_reading)  # Refresh to get the new ID

            return {
                "message": "Data inserted successfully",
                "inserted_id": sensor_reading.id
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database insertion failed: {str(e)}")
