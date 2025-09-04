import time
from src.core.config import timescale_engine, citydb_engine
from src.db.bases import CityDBBase, TimescaleDBBase


def init_db():
    max_retries = 30
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            print(f"Attempting to initialize databases (attempt {attempt + 1}/{max_retries})...")
            
            print("Initializing TimescaleDB...")
            TimescaleDBBase.metadata.create_all(timescale_engine)

            print("Initializing CityDB...")
            CityDBBase.metadata.create_all(citydb_engine)

            print("Database initialization complete.")
            return
        except Exception as e:
            print(f"Database initialization failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Starting API without database initialization.")
                # Don't raise the exception, just log it and continue
                print(f"Database initialization failed after {max_retries} attempts: {str(e)}")
