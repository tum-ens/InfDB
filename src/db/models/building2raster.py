from sqlmodel import Field
from src.db.bases import CityDBBase


# this is just for a reference Building2Raster
# this is not the correct model
# but we would like to provide a minimalistic model just for Building2Raster
class Building(CityDBBase, table=True):
    __tablename__ = "buildings"
    __table_args__ = {"schema": "general"}

    feature_id: int = Field(primary_key=True)


class Building2Raster(CityDBBase, table=True):
    __tablename__ = "building_2_raster"
    __table_args__ = {"schema": "general"}

    building_id: int = Field(nullable=False, primary_key=True)
    raster_id: str = Field(foreign_key="general.raster.id", nullable=False, primary_key=True)
