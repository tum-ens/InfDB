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
COMPOSE_PROFILES=db # (1)

# All profiles
# COMPOSE_PROFILES=db,admin,notebook,qwc,api # (2)

# ==============================================================================
# BASE CONFIGURATION
# ==============================================================================
# Base name for the project (used in network names and data paths)
BASE_NAME=infdb-demo # (3)

# ==============================================================================
# POSTGRESQL DATABASE (Core Service)
# ==============================================================================
# Profile: db

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
SERVICES_JUPYTER_TOKEN=infdb # (19)

# Path to notebook files
SERVICES_JUPYTER_PATH_BASE=../src/notebooks/ # (20)


# ==============================================================================
# QGIS WEB CLIENT (QWC)
# ==============================================================================
# Profile: qwc

# Port for QWC web interface
SERVICES_QWC_EXPOSED_PORT_GUI=80 # (21)

# Port for QWC internal database
SERVICES_QWC_EXPOSED_PORT_DB=5434 # (22)

# Password for QWC PostgreSQL database
SERVICES_QWC_POSTGRES_PASSWORD=infdb # (23)

# JWT secret key for QWC (change this for production!)
JWT_SECRET_KEY=change-me-in-production # (24)
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
15. **PyGeoAPI Host**: Base URL for PyGeoAPI local: `localhost`, remote: `DOMAIN` or `IP-ADDRESS-OF-REMOTE-HOST`.
16. **PostgREST Port**: Port that exposes outside of docker.
17. **Jupyter Port**: Port that exposes Jupyter outside of Docker.
18. **Jupyter Lab**: Enables JupyterLab interface (`yes`/`no`).
19. **Jupyter Token**: Authentication token for Jupyter access.
20. **Jupyter Path**: Base path to notebook files.
21. **QWC GUI Port**: Port that exposes the QWC web interface.
22. **QWC DB Port**: Port that exposes the QWC internal database.
23. **QWC DB Password**: Password for QWC PostgreSQL database.
24. **JWT Secret**: Secret key used by QWC JWT authentication (must be changed for production).

## Detailed configuration guide

Use this section as a practical checklist when editing `.env`.

### 1) Choose service profiles (`COMPOSE_PROFILES`)

The `COMPOSE_PROFILES` variable controls which containers are started.

- Minimal setup (database only):

```env
COMPOSE_PROFILES=db
```

- Typical local development setup:

```env
COMPOSE_PROFILES=db,admin,api,notebook
```

- Full setup (all services):

```env
COMPOSE_PROFILES=db,admin,notebook,qwc,api
```

Only enable what you need. Fewer profiles mean faster startup and fewer port conflicts.

### 2) Set a unique project name (`BASE_NAME`)

`BASE_NAME` is used in container, network, and volume naming.

```env
BASE_NAME=infdb-demo
```

If multiple InfDB instances run on the same machine, give each one a different value (for example `infdb-city-a`, `infdb-city-b`).

### 3) Configure PostgreSQL core settings

These values are required for all setups:

```env
SERVICES_POSTGRES_DB=infdb
SERVICES_POSTGRES_USER=infdb_user
SERVICES_POSTGRES_PASSWORD=change-this-password
SERVICES_POSTGRES_HOST=host.docker.internal
SERVICES_POSTGRES_EXPOSED_PORT=54328
SERVICES_POSTGRES_EPSG=25832
```

Recommendations:

- Use a strong password for `SERVICES_POSTGRES_PASSWORD`.
- Keep the default host unless you know you need another one.
- Change `SERVICES_POSTGRES_EXPOSED_PORT` if `54328` is already in use.
- Set `SERVICES_POSTGRES_EPSG` to the CRS your project uses.

### 4) Configure optional services

Only relevant if their profile is enabled.

#### pgAdmin (`admin` profile)

```env
SERVICES_PGADMIN_DEFAULT_EMAIL=admin@example.com
SERVICES_PGADMIN_DEFAULT_PASSWORD=change-this-password
SERVICES_PGADMIN_EXPOSED_PORT=82
```

- Change credentials for any non-temporary setup.
- If port `82` is occupied, select a free port (for example `8082`).

#### API services (`api` profile)

```env
SERVICES_API_PORT=8000
SERVICES_PYGEOAPI_PORT=8001
SERVICES_PYGEOAPI_BASE_HOST=localhost
SERVICES_POSTGREST_PORT=8002
```

- Keep ports distinct.
- For remote access, set `SERVICES_PYGEOAPI_BASE_HOST` to your host/domain.

#### Jupyter (`notebook` profile)

```env
SERVICES_JUPYTER_EXPOSED_PORT=8888
SERVICES_JUPYTER_ENABLE_LAB=yes
SERVICES_JUPYTER_TOKEN=change-this-token
SERVICES_JUPYTER_PATH_BASE=../src/notebooks/
```

- Always change the Jupyter token.
- Ensure `SERVICES_JUPYTER_PATH_BASE` exists and is readable.

#### QWC (`qwc` profile)

```env
SERVICES_QWC_EXPOSED_PORT_GUI=80
SERVICES_QWC_EXPOSED_PORT_DB=5434
SERVICES_QWC_POSTGRES_PASSWORD=change-this-password
JWT_SECRET_KEY=replace-with-long-random-secret
```

- `JWT_SECRET_KEY` should be long and random in production.
- Avoid commonly used host ports if conflicts occur.

### 5) Validate before startup

Before running Docker Compose:

1. Confirm all required variables for enabled profiles are set.
2. Verify every exposed port is free.
3. Replace all default passwords/tokens/secrets.
4. Save the file as UTF-8 and keep variable names unchanged.

Then start the stack as usual.