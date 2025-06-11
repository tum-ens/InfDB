from sqlmodel import Field
from datetime import datetime
from typing import Optional
from src.db.bases import TimescaleDBBase


class WeatherReading(TimescaleDBBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    raster_id: str = Field(index=True)
    timestamp: datetime
    sensor_name: str = Field(index=True)
    value: float
