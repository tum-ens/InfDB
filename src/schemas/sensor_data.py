from pydantic import BaseModel, Field
from datetime import datetime

class SensorData(BaseModel):
    timestamp: datetime
    sensor_id: int = Field(gt=0, description="Sensor ID must be a positive integer")
    value: float = Field(ge=0, description="Value must be a non-negative number")
