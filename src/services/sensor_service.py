from fastapi import HTTPException
from src.db.models import SensorReading
from src.schemas.sensor_data import SensorData
from sqlmodel import Session, select
from src.core.db_config import timescale_engine

class SensorService:
    def insertSensorData(self, data: SensorData):
        try:
            with Session(timescale_engine) as session:
                # Create a new SensorReading record
                sensor_reading = SensorReading(
                    timestamp=data.timestamp,
                    gml_id=data.gml_id,
                    sensor_name=data.sensor_name,
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
        

    def getByGmlId(self, gml_id: str):
        try:
            with Session(timescale_engine) as session:
                # Query the database using session.exec()
                statement = select(SensorReading).where(SensorReading.gml_id == gml_id)
                sensor_readings = session.exec(statement).all()
                
                if not sensor_readings:
                    raise HTTPException(status_code=404, detail=f"No sensor data found for gml_id: {gml_id}")
                
                # Return the sensor readings
                return {
                    "message": "Data retrieved successfully",
                    "data": [
                        {
                            "id": reading.id,
                            "timestamp": reading.timestamp,
                            "gml_id": reading.gml_id,
                            "sensor_name": reading.sensor_name,
                            "value": reading.value
                        } for reading in sensor_readings
                    ]
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
