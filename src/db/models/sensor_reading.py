from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class SensorReading(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime
    sensor_id: int
    value: float
