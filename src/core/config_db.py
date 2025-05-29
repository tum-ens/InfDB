from sqlalchemy import create_engine
from src.core import config

environment = config.get_value(["base", "environment"])
# this check is important because in the network with docker containers we cannot use
# exposed ports and we have to provide the service name
is_local = (environment == "localhost")
# CityDB Configuration
citydb_host = "127.0.0.1" if is_local else config.get_value(["citydb", "host"])
citydb_port = config.get_value(["citydb", "port"]) if is_local else 5432
citydb_db = config.get_value(["citydb", "db"])
citydb_user = config.get_value(["citydb", "user"])
citydb_password = config.get_value(["citydb", "password"])
epsg = config.get_value(["citydb", "epsg"])


# TimescaleDB Configuration
timescale_host = config.get_value(["timescaledb", "host"])
timescale_port = config.get_value(["timescaledb", "port"])
timescale_user = config.get_value(["timescaledb", "user"])
timescale_password = config.get_value(["timescaledb", "password"])
timescale_db = config.get_value(["timescaledb", "db"])


# Build connection URLs
timescale_url = f"postgresql://{timescale_user}:{timescale_password}@{timescale_host}:{timescale_port}/{timescale_db}"
citydb_url = f"postgresql://{citydb_user}:{citydb_password}@{citydb_host}:{citydb_port}/{citydb_db}"

# Create engines
timescale_engine = create_engine(timescale_url)
citydb_engine = create_engine(citydb_url)
