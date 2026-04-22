---
icon: material/rocket-launch
---
# Deployment :material-rocket-launch:

The InfDB platform is designed for easy deployment using provided bash scripts that abstract complex Docker Compose commands.

!!! warning "Prerequisite"
    Ensure that **Docker** and **Docker Compose** are installed and running on your system.

## Management Commands

### Start InfDB
To start the configured InfDB services:

```bash
bash infdb.sh start
```

!!! info "Persistence"
    InfDB services will continue running in the background until manually stopped, even if the terminal is closed.

## Data Import

The **infdb-import** service usually runs automatically on startup if configured. To trigger a manual import run without restarting the entire stack:

```bash
bash infdb.sh import
```

### Stop InfDB
To stop all running services **without** deleting data:

```bash
bash infdb.sh stop
```

### Remove InfDB
To stop services **and** delete all stored data (reset):

```bash
bash infdb.sh remove PROFILE_NAME
```
PROFILE_NAME can be one of the following, depending on your setup:

- `db` (database)
- `opendata` (downloaded import data)
- `*` (both database and import data)

!!! danger "Data Loss"
    This command will permanently remove all data stored in the database volumes.