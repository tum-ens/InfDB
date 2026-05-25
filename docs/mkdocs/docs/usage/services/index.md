---
icon: material/cogs
---
# Services
![alt text](../../usage/services.png)

- [infdb-db](infdb-db.md): Core PostgreSQL database with PostGIS, timescaledb, and pgrouting extensions; handles all central storage and queries.
- [infdb-import](infdb-import.md): Automates the ingestion, structuring, and integration of external open data formats into the platform.
- [pgAdmin](pgadmin.md): Web UI for inspecting schemas, running SQL, managing roles; auto-configured credentials.
- [FastAPI](fastapi.md): REST endpoints with OpenAPI docs and validated access to 3D, geospatial, and time-series data.
- [Jupyter](jupyter.md): Notebook environment for exploratory queries, ETL prototypes, reproducible analysis.
- [QWC2](qwc2.md): Web mapping client for 2D/3D visualization, layer styling, spatial inspection, quick dataset validation.
- [PostgREST](postgrest.md): Auto-generated REST API over PostgreSQL schemas using DB roles for auth; rapid, lightweight data access without extra backend code.
- [pygeoapi](pygeoapi.md): OGC API (Features/Coverages/Processes) server exposing PostGIS data via standards-based JSON & HTML endpoints for interoperable geospatial discovery and querying.
- [Opencloud](opencloud.md): Cloud infrastructure and deployment management for scalable service orchestration and resource provisioning.