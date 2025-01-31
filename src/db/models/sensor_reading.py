from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class SensorReading(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    gml_id: str = Field(index=True)
    timestamp: datetime
    sensor_name: str
    value: float
