API Overview
============

The InfDB API provides a RESTful interface over two main routes for interacting with key data sources:

- **/city** — Serves static 3D city model data, including buildings and their spatial attributes.
- **/weather** — Provides time-series weather data linked to spatial regions using raster IDs, which must be generated beforehand.

The API uses JSON-formatted requests and responses.

Endpoints
---------

When running the application locally, interactive API documentation is available at:

Swagger UI: http://localhost:8000/docs

City Raster Endpoints
---------------------

- **POST /city/rasters?resolution={resolution}**

  Creates new rasters for geospatial data using the specified ``resolution`` in meters (e.g., 100 or 1000).

- **GET /city/rasters?resolution={resolution}**

  Lists all existing rasters generated for the given ``resolution`` in meters.

- **GET /city/rasters/building/{building_id}?resolution={resolution}**

  Retrieves the raster that contains the building identified by ``building_id``, based on the specified ``resolution`` in meters.

Weather Data Endpoints
----------------------

- **POST /weather-data/{resolution}**

  Inserts historical weather data for the specified ``resolution``.

  **Request Body:**

  - ``dateRange`` — object with ``startDate`` and ``endDate``
  - ``sensorNames`` — list of sensor names matching the data provider

- **GET /weather-data/{resolution}**

  Retrieves weather data linked to the specified ``resolution``.

  **Query Parameters:**

  - ``buildingId`` *(optional)*
  - ``startTime`` *(optional)*
  - ``endTime`` *(optional)*


Error Handling
--------------

The API uses standard HTTP status codes:

- **200 OK** – Request was successful  
- **201 Created** – Resource created  
- **400 Bad Request** – Malformed request  
- **404 Not Found** – Resource not found  
- **422 Unprocessable Entity** – Validation errors  
- **500 Internal Server Error** – Server-side failure  
  
Authentication
--------------

Authentication is not yet implemented. Planned methods include:

- API keys or OAuth2  
- Dependency injection via FastAPI  
- Scoped tokens for protected routes  

Rate Limiting
-------------

Not yet implemented.
