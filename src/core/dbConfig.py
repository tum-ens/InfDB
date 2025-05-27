from sqlmodel import create_engine
from .config import config

# TimescaleDB Configuration
timescale_user = config["timescaledb"]["user"]
timescale_password = config["timescaledb"]["password"]
timescale_host = config["timescaledb"]["host"]
timescale_port = config["timescaledb"]["port"]
timescale_db = config["timescaledb"]["db"]

# CityDB Configuration
citydb_user = config["citydb"]["user"]
citydb_password = config["citydb"]["password"]
citydb_host = config["citydb"]["host"]
citydb_port = config["citydb"]["port"]
citydb_db = config["citydb"]["db"]


# Build connection URLs
timescale_url = f"postgresql://{timescale_user}:{timescale_password}@{timescale_host}:{timescale_port}/{timescale_db}"
citydb_url = f"postgresql://{citydb_user}:{citydb_password}@{citydb_host}:{citydb_port}/{citydb_db}"

# Create engines
timescale_engine = create_engine(timescale_url, echo=True)
citydb_engine = create_engine(citydb_url, echo=True)
