from sqlalchemy.orm import registry
from sqlmodel import SQLModel


class TimescaleDBBase(SQLModel, registry=registry()):
    pass


class CityDBBase(SQLModel, registry=registry()):
    pass
