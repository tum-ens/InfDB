from sqlmodel import Field
from src.db.bases import CityDBBase


# this is just for a reference Building2Raster
# this is not the correct model
# but we would like to provide a minimalistic model just for Building2Raster
class Building(CityDBBase, table=True):
    __tablename__ = "building"
    id: int = Field(primary_key=True)


class Building2Raster(CityDBBase, table=True):
    __tablename__ = "building_2_raster"

    building_id: int = Field(foreign_key="building.id", nullable=False, primary_key=True)
    raster_id: int = Field(foreign_key="raster.id", nullable=False, primary_key=True)

# when querying i have to join by reaster and filter by resolution column on raster table
