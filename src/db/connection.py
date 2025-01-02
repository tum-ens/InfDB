from sqlmodel import SQLModel
from src.core.db_config import timescale_engine, citydb_engine

def init_db():
    try:
        print("Initializing TimescaleDB...")
        SQLModel.metadata.create_all(timescale_engine)

        print("Initializing CityDB...")
        SQLModel.metadata.create_all(citydb_engine)

        print("Database initialization complete.")
    except Exception as e:
        raise RuntimeError(f"Database initialization failed: {str(e)}")
