# System Overview

InfDB is designed as a comprehensive database system for creating digital twins of energy infrastructure with integrated geospatial and
time-series capabilities. The system architecture follows a layered approach with clear separation of concerns.

The core of the system consists of a PostgreSQL database with specialized extensions (TimescaleDB, PostGIS, 3DCityDB) to handle
different types of data. The application layer is built with FastAPI, providing a RESTful interface to interact with the database.

InfDB is a data integration platform that combines **static 3D city models** with **dynamic time-series data**. It connects **3DCityDB** and **TimescaleDB** through a raster-based spatial resolution approach.

Raster grids are generated at specified resolutions (e.g., 100 m, 1 000 m), using official grid IDs from the [Federal Agency for Cartography and Geodesy(BKG)]
(https://gdz.bkg.bund.de/index.php/default/open-data/geographische-gitter-fur-deutschland-in-lambert-projektion-geogitter-inspire.html).

Each building is assigned to one or more raster cells depending on resolution. Since weather data is indexed by raster ID, this allows InfDB to efficiently fetch spatially relevant time-series data (e.g., weather history) for any given building.

## Component Architecture

InfDB is composed of the following main components:

1.  **Database Layer** PostgreSQL with extensions for specialized data types:
    -   TimescaleDB: Handles time-series data efficiently
    -   PostGIS: Provides geospatial capabilities
    -   3DCityDB: Supports urban modeling and 3D city data
2.  **API Layer** FastAPI-based RESTful interface:
    -   City Router: Handles geospatial data and building information
    -   Weather Router: Manages time-series weather data
3.  **Service Layer** Business logic implementation:
    -   CityDB Service: Handles operations related to city data
    -   Weather Service: Manages weather data operations
4.  **Repository Layer** Data access layer:
    -   CityDB Repository: Handles database operations for city data
    -   Weather Repository: Manages database operations for weather data
5.  **Model Layer** Data models and schemas:
    -   Database Models: SQLModel classes for database entities
    -   Schemas: Pydantic models for data validation and serialization
6.  **External Integrations** Connections to external services:
    -   Weather API: Integration with external weather data providers

## Data Flow

The data flow in InfDB follows these general patterns:

1.  **Geospatial Data Flow**: External GIS data → 3DCityDB → CityDB
    Repository → CityDB Service → API
2.  **Time-Series Data Flow**: External Weather API → Weather Service →
    Weather Repository → TimescaleDB → API
3.  **Energy Infrastructure Data Flow**: Energy Network Models →
    PostgreSQL → Repository Layer → Service Layer → API

## Design Decisions

The following key design decisions have shaped the architecture of
InfDB:

1.  **PostgreSQL with Extensions** A single database engine with
    extensions was chosen to simplify deployment and still support
    specialized needs.
2.  **FastAPI Framework** FastAPI offers high performance, async
    support, and built-in OpenAPI documentation.
3.  **SQLModel ORM** SQLModel merges SQLAlchemy and Pydantic benefits,
    providing both ORM features and validation.
4.  **Layered Architecture** The clear separation between API, service,
    repository, and model layers improves testability and scalability.
5.  **Docker Containerization** Docker is used to manage the complex
    multi-extension PostgreSQL setup and ensure reproducible
    environments.

## Database Schema

InfDB separates data modeling across two databases: **3DCityDB** and
**TimescaleDB**, each initialized independently using SQLModel with a
dedicated base class.

### Schema Initialization

The database tables are registered and created through dedicated base
classes to maintain registry isolation.

Defined in `src/db/bases.py`:

``` python
from sqlalchemy.orm import registry
from sqlmodel import SQLModel

class TimescaleDBBase(SQLModel, registry=registry()):
    pass

class CityDBBase(SQLModel, registry=registry()):
    pass
```

Defined in `src/db/connection.py`:

``` python
    from src.core.config import timescale_engine, citydb_engine
    from src.db.bases import CityDBBase, TimescaleDBBase

    TimescaleDBBase.metadata.create_all(timescale_engine)
    CityDBBase.metadata.create_all(citydb_engine)
```

### 3DCityDB Schema

InfDB extends the CityGML schema with two application-specific tables:

-   **raster**
    -   `raster_id`: unique cell ID (Raster IDs follow BKG conventions.)
    -   `resolution`: spatial resolution (meters)
    -   `geom`: geometry of raster
-   **building_2\_raster**
    -   `building_id`: building reference
    -   `raster_id`: raster reference
    -   Composite key: (`building_id`, `raster_id`)

+------------------------+-----------------------------------------------------------------------------------------+
| **Table**              | **Purpose**                                                                             |
+========================+=========================================================================================+
| **raster**             | Stores raster grid cells. Includes raster_id (PK), resolution, and geom.                |
|                        | The raster_id follows the BKG grid ID convention.                                       |
+------------------------+-----------------------------------------------------------------------------------------+
| **building_2_raster**  | Maps each building_id to one or more raster_id entries. Composite PK on                 |
|                        | (building_id, raster_id). Allows many-to-many relationships.                            |
+------------------------+-----------------------------------------------------------------------------------------+

### TimescaleDB Schema

Weather and sensor data is stored in TimescaleDB.

``` python
class WeatherReading(TimescaleDBBase, table=True):
    raster_id: str = Field(primary_key=True)
    timestamp: datetime = Field(primary_key=True)
    sensor_name: str
    value: float
```

Key fields:

-   `raster_id` -- Links reading to spatial grid
-   `timestamp` -- Observation time
-   `sensor_name` -- Type of sensor
-   `value` -- Measured value


+------------------+--------------------------------------------------------------------------------------------+
| **Table**        | **Purpose**                                                                                |
+==================+============================================================================================+
| **weather_data** | Stores time-stamped sensor readings such as temperature, humidity, and more.               |
|                  | Each record includes raster_id, timestamp, sensor_name, and value.                         |
|                  | Enables querying historical weather data for spatial regions.                              |
+------------------+--------------------------------------------------------------------------------------------+