from pydantic import BaseModel, Field
from datetime import datetime

class SensorData(BaseModel):
    timestamp: datetime
    gml_id: str = Field(min_length=1, description="GML ID has to be provided")
    sensor_name: str = Field(min_length=1, description="Sensor ID must be a positive integer")
    value: float = Field(description="Value must be a non-negative number")
