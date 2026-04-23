---
icon: material/database
---

# infdb-db :material-database:

The core service **infdb-db** hosts the PostgreSQL database with extensions for geospatial, time series and graph data, serving as the central database within the platform. It handles data storage, retrieval, and management, ensuring integrity and high availability for connected services and tools.

## Configuration

The system configuration is managed via environment variables:

```bash title=".env"
# ==============================================================================
# SERVICE ACTIVATION
# ==============================================================================
# Select profiles to activate
COMPOSE_PROFILES=core,...  # (1)

# ==============================================================================
# POSTGRESQL DATABASE (Core Service)
# ==============================================================================
# Profile: core

# Database name
SERVICES_POSTGRES_DB=infdb  # (2)

# Database credentials
SERVICES_POSTGRES_USER=infdb_user   # (3)
SERVICES_POSTGRES_PASSWORD=infdb    # (4)

# Host:Port address from which a container is able to reach the Postgres database
SERVICES_POSTGRES_HOST=host.docker.internal # (5)
SERVICES_POSTGRES_EXPOSED_PORT=54328    # (6)

# EPSG code for spatial reference system (25832 = ETRS89 / UTM zone 32N)
SERVICES_POSTGRES_EPSG=25832    # (7)
```

1.  **Activate database service**: The `core` profile must be included to start the database.
2.  **Database name**: The name of the base PostgreSQL database.
3.  **User**: The admin user for the PostgreSQL database.
4.  **Password**: The admin password for the PostgreSQL database.
5.  **Host**: Internal parameter for Docker networking (usually `host.docker.internal`).
6.  **Port**: The port exposed to the host machine for communicating with other applications.
7.  **EPSG**: The default coordinate reference system (CRS) for the database.