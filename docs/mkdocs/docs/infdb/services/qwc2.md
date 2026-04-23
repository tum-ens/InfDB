---
icon: material/map-legend
---
# QGIS Webclient (QWC2) :material-map-legend:

The **QGIS Web Client 2 (QWC2)** service provides a modern, responsive web application for visualizing and interacting with QGIS projects. It allows users to publish geospatial data stored in the InfDB database to the web, offering capabilities such as layer management, feature information, searching, and map printing. More information can be found on the official [Github Repo](https://github.com/qgis/qwc2/).

## Configuration

The configuration is managed via environment variables:

```bash title=".env"
# ==============================================================================
# SERVICE ACTIVATION
# ==============================================================================
# Select profiles to activate
COMPOSE_PROFILES=...,qwc,...  # (1)

# ==============================================================================
# QWC2 SEVICE
# ==============================================================================
# Profile: qwc

# Port on which the QWC2 is available on the host machine
SERVICES_QWC_EXPOSED_PORT=8088 # (2)
```

1.  **Activate service**: The `qwc` profile must be included to activate the QWC service.
2.  **Port**: The port on which QWC2 is available.

## Access

If you activate the service, it should be available on the default port `SERVICES_QWC_EXPOSED_PORT=8088` via your browser:

=== "Local"
    http://localhost:8088

=== "Remote"
    http://IP-ADDRESS-OF-HOST:8088

## Setup and Usage

### Server Setup

#### Get Configuration Files
```bash
git clone https://gitlab.lrz.de/tum-ens/need/infdb.git
cp -r database/tools/qgis_webclient/ qwc
rm -r database
```

#### Configure Database Connection
Edit `qwc/pg_service.conf` to set your geodatabase connection details:
```ini
[qwc_configdb]
host=qwc-postgis
port=5432
dbname=qwc_services
user=qwc_admin
password=qwc_admin
sslmode=disable

[qwc_geodb]
host=qwc-postgis
port=5432
dbname=qwc_services
user=qwc_service_write
password=qwc_service_write
sslmode=disable

[infdb_postgres]
host=postgres
port=5432
dbname=infdb
user=infdb_user
password=infdb
```

#### Generate JWT Secret
```bash
python3 -c 'import secrets; print("JWT_SECRET_KEY=\"%s\"" % secrets.token_hex(48))' >.env
```

#### Set User and Group IDs
In `qwc/docker-compose.yml`, update `SERVICE_UID` and `SERVICE_GID` to match the UNIX user owning the config files:
```yaml
x-qwc-service-variables: &qwc-service-variables
    SERVICE_UID: 1000
    SERVICE_GID: 1000
```

#### Start Services
```bash
docker compose up -d
```

Then generate service configuration via the admin interface (default credentials: `admin`/`admin`) at `http://[ip_address]:8088/qwc_admin/`.

### Publishing Projects

1. Create and save a QGIS project (`.qgz` format)
2. Upload to the server:
```bash
scp project.qgz [username]@[ip_address]:~/qwc/volumes/qgs-resources/scan/project.qgz
```
3. Open the admin interface and generate the service configuration

### Local Setup

Create `pg_service.conf` with the same database connection details and add its path to the `PGSERVICEFILE` environment variable. This allows you to develop projects locally using the same data source as the server.

### Additional Resources

- [Official QWC Documentation](https://qwc-services.github.io/master/)
- [Official QWC Docker Repo](https://github.com/qwc-services/qwc-docker)
- [Our Customized Version](https://gitlab.lrz.de/tum-ens/need/infdb/-/tree/main/tools/qgis_webclient)