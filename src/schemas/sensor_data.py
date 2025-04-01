from pydantic import BaseModel, Field
from datetime import datetime


class SensorData(BaseModel):
    timestamp: datetime
    raster_id: str = Field(min_length=1, description="Raster Id has to be provided")
    sensor_name: str = Field(min_length=1, description="Sensor ID must be a positive integer")
    value: float = Field(description="Value must be a non-negative number")
