# Database Guidelines

## General Principles

- Follow **database normalization principles** (up to 3NF in most cases)
- Use **appropriate data types** for columns
- Implement **proper indexing strategies** based on query patterns
- Use **foreign key constraints** to maintain referential integrity
- Implement **check constraints** to enforce business rules
- Use **transactions** for operations that must be atomic
- Write **efficient queries** that minimize resource usage
- Document **database schema changes** thoroughly

## PostgreSQL Specifics

- Use **appropriate data types** for columns
- Implement **proper indexing strategies** based on query patterns
- Use **foreign key constraints** to maintain referential integrity
- Implement **check constraints** to enforce business rules
- Use **transactions** for operations that must be atomic
- Write **efficient queries** that minimize resource usage

## Data Import/Export

- Implement standardized procedures for data import and export
- Use transaction-safe import processes to prevent partial imports
- Validate imported data against schema constraints before committing
- Provide clear error reporting for failed imports
- Support both bulk and incremental data imports
- Implement data export in standard formats (CSV, JSON, GeoJSON)
- Document data formats and field mappings for external integrations
- Include metadata with exports (timestamp, version, source)

## TimescaleDB

- Use **hypertables** for time-series data
- Define appropriate **chunk intervals** based on data volume and query patterns
- Implement **retention policies** for historical data
- Use **continuous aggregates** for efficient aggregation queries
- Optimize **time-range queries** by including time constraints

## PostGIS

- Use **appropriate spatial reference systems** (SRID) for geospatial data
- Implement **spatial indexes** for efficient geospatial queries
- Use **spatial functions** for geospatial operations
- Optimize **spatial joins** to minimize computational overhead
- Consider **simplifying geometries** for performance when appropriate

## 3DCityDB

- Follow the **3DCityDB schema** for urban modeling
- Use **appropriate LOD (Level of Detail)** for different use cases
- Implement **proper integration** with other database components
- Optimize **3D queries** for performance
