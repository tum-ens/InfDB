---
icon: material/file-cog
---

# Environment Variables

All central configurations of the InfDB services are stored in the environment file `.env` in the project root. This enables modular configuration of the InfDB services.

!!! note
    If you're using the default configuration, you can skip creating and editing the `.env` configuration file.

Before starting InfDB, you need to create the `.env` configuration file by copying from the template `.env.template`:

```bash
cp .env.template .env
```

Edit the environment file `.env` to customize your InfDB instance settings (database credentials, ports, paths, etc.):

```bash title=".env"
# ==============================================================================
# InfDB Docker Compose Configuration
# ==============================================================================
# This file contains all configuration parameters for the InfDB Docker setup.
# Copy this file to .env and customize the values as needed.
# ==============================================================================

# ==============================================================================
# SERVICE ACTIVATION
# ==============================================================================
# Select profiles to activate

# Base profiles
COMPOSE_PROFILES=core # (1)

# All profiles
# COMPOSE_PROFILES=core,admin,notebook,qwc,api # (2)

# ==============================================================================
# BASE CONFIGURATION
# ==============================================================================
# Base name for the project (used in network names and data paths)
BASE_NAME=infdb-demo # (3)

# ==============================================================================
# POSTGRESQL DATABASE (Core Service)
# ==============================================================================
# Profile: core

# Database name
SERVICES_POSTGRES_DB=infdb  # (4)

# Database credentials
SERVICES_POSTGRES_USER=infdb_user   # (5)
SERVICES_POSTGRES_PASSWORD=infdb    # (6)

# Host:Port address from which a container is able to reach the Postgres database
SERVICES_POSTGRES_HOST=host.docker.internal # (7)
SERVICES_POSTGRES_EXPOSED_PORT=54328    # (8)

# EPSG code for spatial reference system (25832 = ETRS89 / UTM zone 32N)
SERVICES_POSTGRES_EPSG=25832    # (9)


# ==============================================================================
# PGADMIN (Database Administration Interface)
# ==============================================================================
# Profile: admin

# Default login credentials for pgAdmin
SERVICES_PGADMIN_DEFAULT_EMAIL=admin@need.energy # (10)
SERVICES_PGADMIN_DEFAULT_PASSWORD=infdb # (11)

# Port to expose pgAdmin on the host machine
SERVICES_PGADMIN_EXPOSED_PORT=82    # (12)


# ==============================================================================
# FASTAPI (REST API Service)
# ==============================================================================
# Profile: api

# Port for the FastAPI service
SERVICES_API_PORT=8000  # (13)


# ==============================================================================
# PYGEOAPI (OGC API Service)
# ==============================================================================
# Profile: api

# Port for the PyGeoAPI service
SERVICES_PYGEOAPI_PORT=8001 # (14)

# Host IP to run PyGeoAPI on (e.g., localhost or 10.162.28.144)
SERVICES_PYGEOAPI_BASE_HOST=localhost   # (15)


# ==============================================================================
# POSTGREST (PostgreSQL REST API)
# ==============================================================================
# Profile: api

# Port for the PostgREST service
SERVICES_POSTGREST_PORT=8002    # (16)


# ==============================================================================
# JUPYTER NOTEBOOK (Development Environment)
# ==============================================================================
# Profile: notebook

# Port to expose Jupyter on the host machine
SERVICES_JUPYTER_EXPOSED_PORT=8888

# Enable Jupyter Lab interface (yes/no)
SERVICES_JUPYTER_ENABLE_LAB=yes

# Authentication token for Jupyter
SERVICES_JUPYTER_TOKEN=infdb

# Path to notebook files
SERVICES_JUPYTER_PATH_BASE=..src/notebooks/


# ==============================================================================
# QGIS WEB CLIENT (QWC)
# ==============================================================================
# Profile: qwc

# Port for QWC web interface
SERVICES_QWC_EXPOSED_PORT_GUI=80

# Port for QWC internal database
SERVICES_QWC_EXPOSED_PORT_DB=5434

# Password for QWC PostgreSQL database
SERVICES_QWC_POSTGRES_PASSWORD=infdb

# JWT secret key for QWC (change this for production!)
JWT_SECRET_KEY=change-me-in-production
```

1.  **Profiles**: By default only the PostgreSQL core is activated. You can activate services by adding the needed profile name to this list.
2.  **All Profiles**: If you uncomment this line, all services will be activated.
3.  **Project Name**: Change the name to the purpose of your work so that the instance can be clearly recognized. This name needs to be unique.
4.  **DB Name**: Name of base postgres database.
5.  **DB User**: Admin user of postgres database.
6.  **DB Password**: Admin password of postgres database.
7.  **DB Host**: Internal parameter (usually `host.docker.internal`).
8.  **DB Port**: Port that exposes outside of docker and used to communicate with other applications.
9.  **EPSG**: Default coordinate reference system (CRS) for postgres database.
10. **pgAdmin Email**: Admin user of pgAdmin web interface.
11. **pgAdmin Password**: Admin password of pgAdmin web interface.
12. **pgAdmin Port**: Port that exposes outside of docker and used to access via browser.
13. **API Port**: Port that exposes outside of docker and used to communicate with other applications.
14. **PyGeoAPI Port**: Port that exposes outside of docker and used to communicate with other applications.
15. **PyGeoAPI Host**: Base url for pygeoAPI local: "localhost", remote: "DOMAIN" or "IP-ADDRESS-OF-REMOTE-HOST".
16. **PostgREST Port**: Port that exposes outside of docker.