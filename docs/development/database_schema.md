# Database Schema Documentation

This document provides detailed information about the database schema used in the InfDB project, focusing on the developer's perspective.

## Table of Contents
1. [Overview](#overview)
2. [3DCityDB Schema](#3dcitydb-schema)
3. [TimescaleDB Schema](#timescaledb-schema)
4. [Database Models](#database-models)
5. [Relationships](#relationships)
6. [Working with the Database](#working-with-the-database)
7. [Schema Evolution](#schema-evolution)

## Overview

InfDB uses two main databases:

1. **3DCityDB**: A PostgreSQL database with PostGIS extension for storing geospatial data, including buildings, terrain, and rasters.
2. **TimescaleDB**: A PostgreSQL database with TimescaleDB extension for storing time-series data, such as weather measurements.

The databases are connected through a common identifier system based on raster IDs, which allows linking time-series data to specific geographic areas.

## 3DCityDB Schema

### Core Tables

3DCityDB follows the CityGML data model, which includes tables for various city objects such as buildings, roads, and vegetation. The most relevant tables for InfDB are:

- **building**: Stores building information
- **geometry_data**: Stores geometric representations of city objects

### Custom Tables

In addition to the standard 3DCityDB tables, InfDB adds two custom tables:

#### Raster Table

The `raster` table stores information about geographic grid cells:

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR | Primary key, unique identifier for the raster |
| resolution | INTEGER | Resolution in meters (e.g., 100, 1000, 10000, 100000) |
| geom | GEOMETRY(POLYGON) | Geometric representation of the raster cell |

The raster IDs follow the format specified by the German Federal Agency for Cartography and Geodesy (BKG), e.g., "100mN32E43" for a 100-meter resolution raster at coordinates N32, E43.

#### Building to Raster Mapping Table

The `building_2_raster` table maps buildings to rasters:

| Column | Type | Description |
|--------|------|-------------|
| building_id | INTEGER | Foreign key to the building table |
| raster_id | VARCHAR | Foreign key to the raster table |

This table has a composite primary key on (building_id, raster_id) to ensure uniqueness.

## TimescaleDB Schema

### Weather Reading Table

The `weather_reading` table stores time-series weather data:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key, auto-incrementing |
| raster_id | VARCHAR | Foreign key to the raster table in 3DCityDB |
| timestamp | TIMESTAMP | Time of the measurement |
| sensor_name | VARCHAR | Name of the sensor (e.g., "temperature", "humidity") |
| value | FLOAT | Measured value |

This table is configured as a TimescaleDB hypertable, partitioned by the timestamp column for efficient time-series queries.

## Database Models

InfDB uses SQLModel (a combination of SQLAlchemy and Pydantic) to define database models in Python. Here are the main models:

### Raster Model

```python
class Raster(CityDBBase, table=True):
    __tablename__ = "raster"
    __table_args__ = (
        UniqueConstraint("geom", name="geom_unique"),
    )

    id: str | None = Field(default=None, primary_key=True)
    resolution: int = Field(default=None, index=True)
    geom: str = Field(
        sa_column=Column(Geometry(geometry_type="POLYGON", srid=3035), unique=True)
    )
```

### Building to Raster Mapping Model

```python
class Building2Raster(CityDBBase, table=True):
    __tablename__ = "building_2_raster"

    building_id: int = Field(foreign_key="building.id", nullable=False, primary_key=True)
    raster_id: str = Field(foreign_key="raster.id", nullable=False, primary_key=True)
```

### Weather Reading Model

```python
class WeatherReading(TimescaleDBBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    raster_id: str = Field(index=True)
    timestamp: datetime
    sensor_name: str = Field(index=True)
    value: float
```

## Relationships

The database schema has the following key relationships:

1. **Building to Raster**: Many-to-many relationship through the `building_2_raster` table. Each building can be associated with multiple rasters (at different resolutions), and each raster can contain multiple buildings.

2. **Raster to Weather Reading**: One-to-many relationship. Each raster can have multiple weather readings, but each weather reading is associated with exactly one raster.

## Working with the Database

### Connecting to the Database

InfDB uses SQLModel to connect to the databases:

```python
from sqlmodel import create_engine, Session

# Create engines
timescale_engine = create_engine(timescale_url, echo=True)
citydb_engine = create_engine(citydb_url, echo=True)

# Use sessions for database operations
with Session(citydb_engine) as session:
    # Perform operations on 3DCityDB
    pass

with Session(timescale_engine) as session:
    # Perform operations on TimescaleDB
    pass
```

### Querying the Database

#### Using SQLModel

```python
from sqlmodel import select
from src.db.models import Raster, WeatherReading

# Query rasters
with Session(citydb_engine) as session:
    statement = select(Raster).where(Raster.resolution == 100)
    rasters = session.exec(statement).all()

# Query weather readings
with Session(timescale_engine) as session:
    statement = select(WeatherReading).where(
        WeatherReading.raster_id == "100mN32E43",
        WeatherReading.timestamp >= start_time,
        WeatherReading.timestamp <= end_time
    )
    readings = session.exec(statement).all()
```

#### Using Raw SQL

For more complex queries, especially those involving geospatial operations, you may need to use raw SQL:

```python
from sqlalchemy import text

# Query raster centers
with Session(citydb_engine) as session:
    sql = text("""
        SELECT g.id AS rasterId, 
               ST_X(ST_Centroid(ST_Transform(ST_SetSRID(g.geom, 25832), 4326))) AS longitude, 
               ST_Y(ST_Centroid(ST_Transform(ST_SetSRID(g.geom, 25832), 4326))) AS latitude
        FROM raster g
        WHERE g.resolution = :resolution
    """)
    result = session.execute(sql, {"resolution": 100}).mappings().all()
```

### Creating and Updating Records

```python
from src.db.models import WeatherReading
from datetime import datetime

# Create a new weather reading
reading = WeatherReading(
    raster_id="100mN32E43",
    timestamp=datetime.now(),
    sensor_name="temperature",
    value=25.5
)

# Save to database
with Session(timescale_engine) as session:
    session.add(reading)
    session.commit()
    session.refresh(reading)
```

## Schema Evolution

As the project evolves, the database schema may need to change. Here are some guidelines for schema evolution:

### Adding New Tables

1. Create a new model class in the appropriate file in `src/db/models/`
2. Ensure the model inherits from the correct base class (`CityDBBase` or `TimescaleDBBase`)
3. Add the model to the imports in `src/db/models/__init__.py`
4. The table will be created automatically when the application starts

### Modifying Existing Tables

For simple changes that don't affect existing data:

1. Update the model class in `src/db/models/`
2. The changes will be applied when the application starts

For more complex changes that require data migration:

1. Create a SQL migration script
2. Apply the migration script manually or through a migration tool
3. Update the model class to reflect the new schema

### Best Practices

- Always maintain backward compatibility when possible
- Document schema changes in the project documentation
- Consider the impact on existing data when making schema changes
- Use database migrations for production deployments