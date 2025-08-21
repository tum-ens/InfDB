# Process data

## Prequires
- Docker
- Have database set up with Open Data (see `src/services/loader`)

## Startup
From the root project folder you can start the processor by executing these commands via bash:
```bash
docker compose -f compose.yml up
```

### Source Code
- The folder contains source code to create three tables in the `pylovo_input`:
  - `ways` (street segments)
  - `buildings` (buildings with 2D geometries and other data)
  - `buildings_grid` (100m * 100m grids with census data that overlap with at least one building)
  - `way_names` (street names of ways)
  - `building_addresses` (addresses assigned to buildings)



### Process data
Paths in .env
```yml
CONFIG_INFDB_PATH=../../configs # Path to the configs directory of infDB
```
Settings in /tools/processor/configs/config-processor.yml
```bash
    # on linux and macos
    docker compose -f tools/processor/compose.yml up 

    # on windows
```