# Loader

## Prequires
- Docker
- Have database set up with Open Data

## Startup
From the root project folder you can start the processor by executing these commands via bash:
```bash
# on linux and macos
docker compose -f compose.yml up
```

## Data Sources
The following datasources are available:
- Germany
  - Zensus 2020
  - Basemap
  - TABULA Germany
  - Zip Codes
- Bavaria
  - Buildings (LOD2)

## Source Code
- The folder contains source code ("src/") to create tables in schema "opendata":
- `main.py` start load single data sources in multiple processes
- `configs`
  - test
- `src`
  - `sources` python files for single data sources import
  - `logger.py` logging
  - `utils.py` helper functions
  - `building_addresses` (addresses assigned to buildings)