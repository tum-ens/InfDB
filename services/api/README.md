# FastAPI Application Docker Setup

This directory contains the Docker configuration for the INFDB FastAPI application.

## Quick Start

To run the FastAPI application with all its dependencies:

```bash
# From the project root directory
docker compose up -d
```

This will start:

- CityDB (PostgreSQL database)
- TimescaleDB (Time-series database)
- PgAdmin (Database administration)
- QGIS Web Client
- **FastAPI Application** (available at http://localhost:8000)

## API Endpoints

Once running, you can access:

- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health (if implemented)

## Development

To run only the API service for development:

```bash
# Build and run just the API
docker compose up api -d

# View logs
docker compose logs -f api

# Stop the API
docker compose stop api
```

## Environment Variables

The API service uses these environment variables:

- `DATABASE_URL`: Connection string for CityDB
- `TIMESCALE_URL`: Connection string for TimescaleDB

These are automatically set in the Docker configuration.
