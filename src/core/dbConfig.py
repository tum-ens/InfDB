import os
from dotenv import load_dotenv
from sqlmodel import create_engine

# Load environment variables from .env
load_dotenv()

# TimescaleDB Configuration
timescale_user = os.getenv("TIMESCALE_USER")
timescale_password = os.getenv("TIMESCALE_PASSWORD")
timescale_host = os.getenv("TIMESCALE_HOST")
timescale_port = os.getenv("TIMESCALE_PORT")
timescale_db = os.getenv("TIMESCALE_DB")

# CityDB Configuration
citydb_user = os.getenv("CITYDB_USER")
citydb_password = os.getenv("CITYDB_PASSWORD")
citydb_host = os.getenv("CITYDB_HOST")
citydb_port = os.getenv("CITYDB_PORT")
citydb_db = os.getenv("CITYDB_DB")

# Build connection URLs
timescale_url = f"postgresql://{timescale_user}:{timescale_password}@{timescale_host}:{timescale_port}/{timescale_db}"
citydb_url = f"postgresql://{citydb_user}:{citydb_password}@{citydb_host}:{citydb_port}/{citydb_db}"

# Create engines
timescale_engine = create_engine(timescale_url, echo=True)
citydb_engine = create_engine(citydb_url, echo=True)
