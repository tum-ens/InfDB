from sqlmodel import Field, Column
from sqlalchemy import UniqueConstraint
from geoalchemy2 import Geometry
from src.db.bases import CityDBBase


class Raster(CityDBBase, table=True):
    __tablename__ = "raster"
    __table_args__ = (
        UniqueConstraint("geom", name="geom_unique"),
    )

    id: int | None = Field(default=None, primary_key=True)
    resolution: int = Field(default=None)
    geom: str = Field(
        sa_column=Column(Geometry(geometry_type="POLYGON", srid=4326), unique=True)
    )
