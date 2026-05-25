# InfDB FDW Setup Tool

> Sets up PostgreSQL Foreign Data Wrapper (FDW) to access the central opendata schema from remote InfDB instances without data duplication.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Output](#output)
- [Troubleshooting](#troubleshooting)
- [License and Citation](#license-and-citation)
- [Contact](#contact)

## Overview

The InfDB FDW Setup Tool configures PostgreSQL Foreign Data Wrapper to allow new InfDB instances to access the central "opendata" schema remotely. This eliminates the need to duplicate open data across multiple database instances, ensuring data consistency and reducing storage requirements.

**Problem Solved:**
- Multiple InfDB instances need access to the same open data (buildings, administrative areas, census data, etc.)
- Traditional approach requires importing the same data into each instance
- FDW allows transparent access to centralized data without duplication

**Use Cases:**
- Setting up new InfDB instances that need access to centralized open data
- Maintaining data consistency across multiple analysis environments
- Reducing storage costs by centralizing reference data

## Features

- Automated FDW setup with proper error handling and cleanup
- Configurable connection to central InfDB instance
- Transparent access to remote opendata schema
- Permission management for multi-user access
- Comprehensive logging and troubleshooting

## Prerequisites

Before using this tool, ensure you have:

- infDB instance running (see [infDB documentation](https://infdb.readthedocs.io/))
- Docker and Docker Compose installed
- Access to a central InfDB instance with the "opendata" schema populated
- Network connectivity between local and central InfDB instances

## Installation

### Clone the Repository

This tool is part of the infDB repository:

```bash
# Already included in infDB under tools/infdb-fdw-setup/
cd infdb/tools/infdb-fdw-setup
```

## Configuration

### Configuration File

The tool is configured via `configs/config-infdb-fdw-setup.yml`. Copy the template first:

```bash
cp configs/config-infdb-fdw-setup.yml.template configs/config-infdb-fdw-setup.yml
```

### Configuration Options

Edit `configs/config-infdb-fdw-setup.yml` with your settings. A minimal example:

```yaml
infdb-fdw-setup:
  config-infdb: "config-infdb.yml"
  logging:
    path: "infdb-fdw-setup.log"
    level: "INFO"  # ERROR, WARNING, INFO, DEBUG
  fdw:
    status: active # set to "inactive" to disable FDW setup
    central_db:
      host: "host.docker.internal"  # Central InfDB instance host
      port: 54328                      # Central InfDB instance port
      db: "infdb"                     # Central InfDB database name (usually $SERVICES_POSTGRES_DB)
      user: "citydb_user"             # Central InfDB user
      password: "infdb"               # Central InfDB password
    foreign_schema: "opendata"        # Schema to import via FDW
    local_schema: "opendata_fdw"      # Local schema name for FDW mapping
    read_only: true                   # Defaults to true; set false to allow writes
```

Notes:
- The central database name commonly used in this repository is `infdb` (see `SERVICES_POSTGRES_DB` in the root `.env`). Use the actual name of your central database.
- Ports and hostnames must be reachable from the machine/container running this tool (e.g. `host.docker.internal` when running Docker on macOS).

**Configuration Parameters:**

| Parameter | Description | Example / Recommended | Required |
|--------|-----------------------------|---------|----------|
| `fdw/central_db/host` | Hostname/IP of central InfDB | `host.docker.internal` | Yes |
| `fdw/central_db/port` | Port of central InfDB | `54328` | Yes |
| `fdw/central_db/db` | Database name on central InfDB | `infdb` (or `$SERVICES_POSTGRES_DB`) | Yes |
| `fdw/central_db/user` | Username for central InfDB  | `citydb_user` | Yes |
| `fdw/central_db/password` | Password for central InfDB  | `infdb` | Yes |
| `fdw/foreign_schema` | Schema name on central DB   | `opendata` | Yes |
| `fdw/local_schema` | Local schema name for FDW   | `opendata_fdw` | Yes |
| `fdw/read_only` | Disable writes to foreign tables | `true`  | No |
| `fdw/status` | Enables FDW mapper creation | `active` | Yes |

### Environment Variables

Configure environment variables in `.env`:

```bash
CONFIG_INFDB_PATH=../infdb/configs  # Path to infDB config folder
```

## Usage

### Execution Modes

- **Standard Mode**: Sets up FDW and imports the complete opendata schema
- **Custom Mode**: Modify configuration to import specific schemas or tables

### Quick Start

From the repository root (recommended):

```bash
# Run the FDW setup from repo root
docker compose -f tools/infdb-fdw-setup/compose.yml --profile infdb-fdw-setup up
```

From inside the tool directory:

```bash
cd tools/infdb-fdw-setup
docker compose -f compose.yml --profile infdb-fdw-setup up
```

Notes:
- If you run from the tool directory, use the local `compose.yml` path. If you run from the repository root, use the relative path `tools/infdb-fdw-setup/compose.yml`.
- Ensure the root `.env` is available and readable if your configuration relies on environment variables defined there. When running from the repo root Docker Compose will automatically load `.env` in the same directory. When running from inside `tools/infdb-fdw-setup`, verify the service's `env_file` settings (the compose file can reference `../../.env`).

### Verification

After the container completes successfully, verify the FDW objects and query foreign tables:

```bash
# Open a psql shell in the local Postgres container (adjust container name if different)
docker exec -it infdb-demo-postgres-1 psql -U infdb_user -d infdb
```

Inside psql run:

```sql
-- List the FDW schema and tables
\dn
\dt opendata_fdw.

-- Count imported foreign tables
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'opendata_fdw';

-- Sample query against a foreign table (replace with an existing table name)
SELECT * FROM opendata_fdw.bkg_vg5000_gem LIMIT 5;
```

The `\dt opendata_fdw.` command lists the foreign tables in that schema. If queries return rows, FDW access is working and data is being read from the central InfDB instance.

## Output

### Database Integration

The tool creates the following database objects:

- **Extension**: `postgres_fdw` (enabled if not already present)
- **Foreign Server**: `infdb_central_server` (connection to central DB)
- **User Mapping**: Maps local user to central DB credentials
- **Local Schema**: `opendata_fdw` (contains foreign tables)
- **Foreign Tables**: All tables from central `opendata` schema

### Accessing Foreign Data

After setup, access the centralized opendata via:

```sql
-- Example queries
SELECT * FROM opendata_fdw.buildings;
SELECT COUNT(*) FROM opendata_fdw.administrative_areas;
SELECT * FROM opendata_fdw.census_data WHERE year = 2022;
```

### Output Location

Logs are stored in:
```
infdb-fdw-setup.log
```

## Troubleshooting

### Common Issues

**Issue**: Connection refused to central database
```
psycopg2.OperationalError: could not connect to server
```
**Solution**: Verify central InfDB instance is running and network accessible. Check firewall settings and Docker networking.

---

**Issue**: Permission denied on foreign server
```
ERROR: permission denied for foreign server infdb_central_server
```
**Solution**: Ensure the central database user has appropriate permissions. Check user mapping credentials.

---

**Issue**: Foreign schema import fails
```
ERROR: schema "opendata" does not exist
```
**Solution**: Verify the central InfDB instance has the opendata schema populated with data.

---

**Issue**: Import fails with `relation "..." already exists` (duplicate table)
```
psycopg2.errors.DuplicateTable: relation "basemap_verkehrslinie" already exists
```
**Cause**: A previous run left foreign tables or local objects in the target schema. `IMPORT FOREIGN SCHEMA` attempts to create local foreign tables with the same names and fails.
**Solution**:
- Recommended: The setup script now drops the local target schema and recreates it before importing. Re-run the tool to get a clean import.
- Manual recovery: connect to the local database and drop the local schema before running the tool:

```sql
DROP SCHEMA IF EXISTS opendata_fdw CASCADE;
```

Then re-run the FDW setup.

### Logging

Check logs for detailed error information:
```bash
# View container logs
docker compose logs infdb-fdw-setup

# View application log file
cat infdb-fdw-setup.log
```

### Getting Help

If you encounter issues:
1. Check the logs for error messages
2. Verify configuration settings match your central InfDB instance
3. Ensure network connectivity between instances
4. Test direct connection to central database
5. Review PostgreSQL FDW documentation
6. Open an issue on the repository

## License and Citation

This tool is licensed under the **MIT License** (MIT).  
See [LICENSE](LICENSE) for rights and obligations.  
See the *Cite this repository* function or [CITATION.cff](CITATION.cff) for citation.

Copyright: Technical University of Munich | [MIT](LICENSE)

## Contact

InfDB Development Team  
Technical University of Munich  
Email: infdb@tum.de  

---

**Part of the infDB ecosystem**: [https://infdb.readthedocs.io/](https://infdb.readthedocs.io/)
