# API Overview

InfDB exposes a modular, RESTful API built with **FastAPI**, designed to support spatial and temporal data queries across city models and sensor datasets.

The API enables clients to:

- Generate and access **rasterized spatial grids** for linking buildings to grid cells
- Insert and retrieve **time-series data**, such as weather, sensor readings, or simulation outputs, all linked to spesific raster

The API is built with:

- **FastAPI** for high-performance HTTP services
- **Pydantic** for strict input/output validation
- **OpenAPI** documentation for self-discovery and developer tooling

When the application is running locally, interactive API documentation is available at:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)


## Purpose of Routes

The API is organized into two main route groups:

### `/city`

Handles operations related to **buildings**, **raster grid generation**, and **spatial queries**. These endpoints serve as the bridge between 3D city models and grid-based spatial indexing used throughout InfDB.

### `/weather-data`

Provides access to **time-series data** (weather, simulation results, or other temporal measurements) that are **spatially indexed using raster IDs**. Although initially designed for weather data, the API supports any sensor or time-series dataset linked to a raster cell.

## Endpoints

### City Raster Endpoints (`/city`)

- `POST /city/rasters?resolution={resolution}`  
  Generates raster grids at the specified resolution (in meters). These grids are aligned with official spatial grids (e.g., from BKG) and are used to link buildings to geographic cells.

- `GET /city/rasters?resolution={resolution}`  
  Lists all rasters created at the specified resolution.

- `GET /city/rasters/building/{building_id}?resolution={resolution}`  
  Returns the raster cell(s) that contain the specified building. Useful for spatially linking a building to any raster-indexed dataset.

### Time-Series Data Endpoints (`/weather-data`)

- `POST /weather-data/{resolution}`  
  Inserts time-series sensor data for a given raster resolution.  
  This endpoint is designed for ingesting any temporally indexed data (not just weather), such as simulations, IoT sensor logs, or environmental observations.

  **Payload includes:**
  - `dateRange` — object with `startDate` and `endDate`
  - `sensorNames` — list of sensor types to retrieve and store

- `GET /weather-data/{resolution}`  
  Retrieves time-series data for a specific resolution. Can be filtered by building ID and time range.

  **Query Parameters:**
  - `buildingId` *(optional)* — spatially joins time-series data based on the building's raster
  - `startTime` *(optional)* — ISO timestamp
  - `endTime` *(optional)* — ISO timestamp

## Summary

The InfDB API enables efficient querying and insertion of spatial and temporal data. Its design ensures that:

- Spatial entities (buildings) are easily linked to grid cells
- Time-series data can be indexed, filtered, and queried at multiple resolutions
- The API remains modular and extensible for future data types (e.g., energy demand, mobility traces)

For developer usage and interactive documentation, visit the live API endpoints while the server is running locally.
