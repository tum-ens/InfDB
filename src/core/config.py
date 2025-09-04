import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database URLs from environment variables or defaults
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://citydb_user:infdb@citydb:5432/citydb")
TIMESCALE_URL = os.getenv("TIMESCALE_URL", "postgresql://timescaledb_user:infdb@timescaledb:5433/timescaledb")

# Create database engines
citydb_engine = create_engine(DATABASE_URL)
timescale_engine = create_engine(TIMESCALE_URL)

# Create session factories
CityDBSession = sessionmaker(autocommit=False, autoflush=False, bind=citydb_engine)
TimescaleDBSession = sessionmaker(autocommit=False, autoflush=False, bind=timescale_engine) 