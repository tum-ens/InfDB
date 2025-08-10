API Endpoints Guide
===================

When running the application locally, interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs

City Raster Endpoints
---------------------

.. rubric:: `POST /city/rasters?resolution={resolution}`

Creates rasters for geospatial data at the specified resolution (e.g., `100`, `1000`, `10000`).

.. admonition:: Valid Example
   :class: valid-example

   .. code-block:: bash
      :caption: Request

      curl -X POST "http://127.0.0.1:8000/city/rasters?resolution=10000" \
           -H "accept: application/json" \
           -d ""

   .. code-block:: json
      :caption: Response

      {
        "message": "Raster table filled successfully"
      }

.. admonition:: Invalid Example – Unsupported Resolution
   :class: invalid-example

   .. code-block:: bash
      :caption: Request

      curl -X POST "http://127.0.0.1:8000/city/rasters?resolution=1000000" \
           -H "accept: application/json" \
           -d ""

   .. code-block:: json
      :caption: Response

      {
        "detail": [
          {
            "type": "enum",
            "loc": ["query", "resolution"],
            "msg": "Input should be 100, 1000, 10000 or 100000",
            "input": "1000000",
            "ctx": {
              "expected": "100, 1000, 10000 or 100000"
            }
          }
        ]
      }

.. rubric:: `GET /city/rasters?resolution={resolution}`

Lists all rasters generated for the given resolution.

.. admonition:: Valid Example
   :class: valid-example

   .. code-block:: bash
      :caption: Request

      curl -X GET "http://127.0.0.1:8000/city/rasters?resolution=100000" \
           -H "accept: application/json"

   .. code-block:: json
      :caption: Response

      [
        {
          "rasterid": "100kmN26E40",
          "longitude": 41.6467281659667,
          "latitude": 20.494723184554264
        },
        // additional readings...
      ]

.. admonition:: Invalid Example – No Data Found
   :class: invalid-example

   .. code-block:: bash
      :caption: Request

      curl -X GET "http://127.0.0.1:8000/city/rasters?resolution=10000000"

   .. code-block:: json
      :caption: Response

      {
        "detail": "No data found"
      }

.. rubric:: `GET /city/rasters/building/{building_id}?resolution={resolution}`

Finds the raster containing a specific building at a given resolution.

.. admonition:: Valid Example
   :class: valid-example

   .. code-block:: bash
      :caption: Request

      curl -X GET "http://127.0.0.1:8000/city/rasters/building/5?resolution=100000" \
           -H "accept: application/json"

   .. code-block:: json
      :caption: Response

      {
        "building_id": 5,
        "raster_id": "100kmN27E43",
        "longitude": 44.22127881529021,
        "latitude": 20.710226069778226
      }

.. admonition:: Invalid Example – Building Not Found
   :class: invalid-example

   .. code-block:: bash
      :caption: Request

      curl -X GET "http://127.0.0.1:8000/city/rasters/building/12?resolution=10000" \
           -H "accept: application/json"

   .. code-block:: json
      :caption: Response

      {
        "detail": "No data found"
      }

Weather Data Endpoints
----------------------

.. rubric:: `POST /weather/weather-data/{resolution}`

Inserts historical weather data for a raster at the given resolution.

.. admonition:: Valid Example
   :class: valid-example

   .. code-block:: bash
      :caption: Request

      curl -X POST "http://127.0.0.1:8000/weather/weather-data/100000" \
           -H "accept: application/json" \
           -H "Content-Type: application/json" \
           -d '{
                 "dateRange": {
                   "startDate": "2025-07-05",
                   "endDate": "2025-07-06"
                 },
                 "sensorNames": [
                   "temperature"
                 ]
               }'

   .. code-block:: json
      :caption: Response

      {
        "message": "Data processed"
      }

.. admonition:: Invalid Example – Invalid Sensor Name
   :class: invalid-example

   .. code-block:: json
      :caption: Response

      {
        "error": "Invalid weather variable requested. Please check the input parameters.",
        "details": {
          "error": true,
          "reason": "Data corrupted at path ''. Cannot initialize SurfacePressureAndHeightVariable<...> from invalid String value string."
        }
      }

.. note::

   Weather data requests may take some time depending on resolution and time range,  
   as data must be fetched, parsed, and stored into the database.

.. rubric:: `GET /weather/weather-data/{resolution}`

Retrieves weather data for the given resolution.

Optional query parameters:

- ``buildingId`` (required for building-specific queries)
- ``startTime``
- ``endTime``

.. admonition:: Valid Example
   :class: valid-example

   .. code-block:: bash
      :caption: Request

      curl -X GET "http://127.0.0.1:8000/weather/weather-data/100000?buildingId=5" \
           -H "accept: application/json"

   .. code-block:: json
      :caption: Response

      [
        {
          "sensor_name": "temperature",
          "id": 23618,
          "raster_id": "100kmN27E43",
          "timestamp": "2025-07-05T00:00:00",
          "value": 31.3400001526
        },
        // additional readings...
      ]

.. admonition:: Invalid Example – Raster Not Found
   :class: invalid-example

   .. code-block:: bash
      :caption: Request

      curl -X GET "http://127.0.0.1:8000/weather/weather-data/10000" \
           -H "accept: application/json"

   .. code-block:: json
      :caption: Response

      {
        "detail": "Raster center not found"
      }
