# Load data

## Prequires
- Docker
- Have database set up with Open Data

### Source Code
- The folder contains source code ("src/") to create tables in schema "opendata":
  - `main.py` start load single data sources in multiple processes
  - `sources` python files for single data sources import
  - `logger.py` logging
  - `utils.py` helper functions
  - `building_addresses` (addresses assigned to buildings)

### Startup
From the root project folder you can start the processor by executing these commands via bash:
```bash
# on linux and macos
docker compose -f tools/loader/compose-setup.yml up
docker compose -f tools/loader/compose.yml --env-file tools/loader/.env up
```