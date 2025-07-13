Architecture
============

This chapter outlines the architecture of **InfDB**.

System Overview
----------------

InfDB combines static **3D city models** with dynamic **time-series** information. It acts as a bridge between **3DCityDB** and **TimescaleDB** by introducing a raster-based resolutions.

.. note::

   For every required resolution (``100 m``, ``1 000 m``, ``10 000 m``, ``100 000 m``), InfDB creates a matching grid in the ``raster`` table.  
   The grid-cell IDs follow the official scheme published by the `Federal Agency for Cartography and Geodesy (BKG) <https://gdz.bkg.bund.de/index.php/default/open-data/geographische-gitter-fur-deutschland-in-lambert-projektion-geogitter-inspire.html>`_.

Each building is connected to one or more raster cells. Weather data is stored using these raster IDs, so the system can quickly find all past weather information related to a building.

Components
----------

+---------------------+-----------------------------------------------------------------------------------------------------+
| **Component**       | **Role**                                                                                            |
+=====================+=====================================================================================================+
| **3DCityDB**        | PostgreSQL/PostGIS database storing the static CityGML city model                                   |
|                     | (buildings, terrain, geometry).                                                                     |
+---------------------+-----------------------------------------------------------------------------------------------------+
| **TimescaleDB**     | PostgreSQL extension optimised for high-volume time-series data                                     |
|                     | (e.g., weather measurements).                                                                       |
+---------------------+-----------------------------------------------------------------------------------------------------+
| **FastAPI backend** | Python web service that exposes REST endpoints for read/write access to both databases.             |
+---------------------+-----------------------------------------------------------------------------------------------------+

Database Schema
---------------

3DCityDB
^^^^^^^^^

+------------------------+-----------------------------------------------------------------------------------------+
| **Table**              | **Purpose**                                                                             |
+========================+=========================================================================================+
| **raster**             | Stores raster grid cells. Includes raster_id (PK), resolution, and geom.                |
|                        | The raster_id follows the BKG grid ID convention.                                       |
+------------------------+-----------------------------------------------------------------------------------------+
| **building_2_raster**  | Maps each building_id to one or more raster_id entries. Composite PK on                 |
|                        | (building_id, raster_id). Allows many-to-many relationships.                            |
+------------------------+-----------------------------------------------------------------------------------------+


TimescaleDB
^^^^^^^^^^^

+------------------+--------------------------------------------------------------------------------------------+
| **Table**        | **Purpose**                                                                                |
+==================+============================================================================================+
| **weather_data** | Stores time-stamped sensor readings such as temperature, humidity, and more.               |
|                  | Each record includes raster_id, timestamp, sensor_name, and value.                         |
|                  | Enables querying historical weather data for spatial regions.                              |
+------------------+--------------------------------------------------------------------------------------------+

.. image:: ../../img/db_tables.png
   :alt: InfDB Architecture
   :align: center
