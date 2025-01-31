from pydantic import BaseModel, Field
from datetime import datetime


class CityObjectInput(BaseModel):
    objectclass_id: int = Field(..., description="The object class ID")
    gmlid: str = Field(..., description="The GML ID")
    creation_date: datetime = Field(default_factory=datetime.now, description="Creation date")
