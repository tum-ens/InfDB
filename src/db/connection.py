from src.core.config import timescale_engine, citydb_engine
from src.db.bases import CityDBBase, TimescaleDBBase


def init_db():
    try:
        print("Initializing TimescaleDB...")
        TimescaleDBBase.metadata.create_all(timescale_engine)

        print("Initializing CityDB...")
        CityDBBase.metadata.create_all(citydb_engine)

        print("Database initialization complete.")
    except Exception as e:
        raise RuntimeError(f"Database initialization failed: {str(e)}")
