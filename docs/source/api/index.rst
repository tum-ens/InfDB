API Overview
============

The InfDB API provides a RESTful interface over two main routes for interacting with two main data sources:

- **/city** — Serves static 3D city model data, including buildings and their spatial attributes.
- **/weather** — Provides time-series weather data linked to spatial regions using raster IDs which has to be generated beforehand.

The API uses JSON-formatted requests and responses.

Endpoints
---------

The API exposes various endpoints for managing both geospatial and weather data resources.
When you run the application locally, you can reach those endpoint documentations, at this url: http://127.0.0.1:8000/docs

City Raster Endpoints
---------------------------

- **POST /city/rasters?resolution={resolution}**

  Creates new rasters for geospatial data using the specified **resolution** in meters (e.g., 100 or 1000).

- **GET /city/rasters?resolution={resolution}**

  Lists all existing rasters generated for the given **resolution** in meters.

- **GET /city/rasters/building/{building_id}?resolution={resolution}**

  Retrieves the raster that contains the building identified by **building_id**, based on the given **resolution** in meters.

Weather Data Endpoints
---------------------------

- **POST /weather-data/{resolution}**

  Inserts historical weather data for the specified **resolution**.

  **Request Body:**

  - **dateRange** — object with **startDate** and **endDate**
  - **sensorNames** — list of sensor names matching the data provider

- **GET /weather-data/{resolution}**

  Retrieves weather data linked to the specified **resolution**.

  **Query Parameters:**
  - **buildingId** *(optional)*
  - **startTime** *(optional)*
  - **endTime** *(optional)*




Authentication
--------------

Not yet implemented.

Rate Limiting
-------------

Not yet implemented.
