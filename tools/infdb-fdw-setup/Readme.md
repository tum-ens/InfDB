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

Edit `configs/config-infdb-fdw-setup.yml` with your settings:

```yaml
infdb-fdw-setup:
  config-infdb: "config-infdb.yml"
  logging:
    path: "infdb-fdw-setup.log"
    level: "INFO"  # ERROR, WARNING, INFO, DEBUG
  hosts:
    postgres:
      user: None
      password: None
      db: None
      host: None
      exposed_port: None
      epsg: None
  fdw:
    central_db:
      host: "host.docker.internal"  # Central InfDB instance host
      port: 5432  # Central InfDB instance port
      db: "postgres"  # Central InfDB database name
      user: "citydb_user"  # Central InfDB user
      password: "infdb"  # Central InfDB password
    foreign_schema: "opendata"  # Schema to import via FDW
    local_schema: "opendata_fdw"  # Local schema name for FDW mapping
```

**Configuration Parameters:**

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `fdw/central_db/host` | Hostname/IP of central InfDB | `host.docker.internal` | Yes |
| `fdw/central_db/port` | Port of central InfDB | `5432` | Yes |
| `fdw/central_db/db` | Database name on central InfDB | `postgres` | Yes |
| `fdw/central_db/user` | Username for central InfDB | `citydb_user` | Yes |
| `fdw/central_db/password` | Password for central InfDB | `infdb` | Yes |
| `fdw/foreign_schema` | Schema name on central DB | `opendata` | Yes |
| `fdw/local_schema` | Local schema name for FDW | `opendata_fdw` | Yes |

### Environment Variables

Configure environment variables in `.env`:

```bash
CONFIG_INFDB_PATH=../infdb/configs  # Path to infDB config folder
```

## Usage

### Run the Tool

Execute the tool using Docker Compose:

```bash
docker compose -f tools/infdb-fdw-setup/compose.yml up
```

For standalone execution:
```bash
docker compose up
```

### Execution Modes

- **Standard Mode**: Sets up FDW and imports the complete opendata schema
- **Custom Mode**: Modify configuration to import specific schemas or tables

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
