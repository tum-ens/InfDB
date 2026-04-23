# API Reference

The InfDB platform offers several APIs to interact with the database and its services. Below is an overview of the main APIs available:

## [Python Package pyinfdb](pyinfdb/index.md)
The python package `pyinfdb` provides set of modules, classes and functions for database access, configuration management, logging and data handling. The central idea is to provide standard methods to interact with InfDB in order to simplify the interaction with InfDB.

See [API -> pyinfdb](pyinfdb/index.md) for detailed usage instructions.

## FastAPI
The FastAPI is currently only forwarding to the PostgREST service.

- **Default endpoint:** `http://host-address:8000`
- **Default docs endpoint:** `http://host-address:8000/docs`

See the official [FastAPI documentation](https://fastapi.tiangolo.com/) for more details.

## pygeoapi
The pygeoAPI provides OGC compliant API for geospatial data sharing and discovery. It supports standards-based access to geospatial data, making it compatible with GIS clients and web mapping applications. It also supports multiple data formats and includes interactive API documentation for testing endpoints.

- **Default endpoint:** `http://host-address:8001`
- **Default docs endpoint:** `http://host-address:8001/openapi`

See the official [pygeoapi documentation](https://pygeoapi.io/) for more details.

## PostgREST
The PostgREST API provides an automatic REST API for PostgreSQL databases. It uses this for standard CRUD operations on tables and views. PostgREST automatically generates interactive Swagger documentation at `/docs` endpoint, allowing you to explore and test all available endpoints directly from your browser.

- **Default endpoint:** `http://host-address:8002`
- **Default docs endpoint:** `http://host-address:8002/docs`

See the official [PostgREST documentation](https://postgrest.org/en/stable/) for more details.