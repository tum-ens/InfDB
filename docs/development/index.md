# Repository Structure

The InfDB project is modular, clearly layered, and designed to separate responsibilities across core services, configuration, documentation, and deployment. Below is a breakdown of major directories along with developer-relevant details.

## Main Application Package (`src/`)

Contains all core logic for the FastAPI backend including API endpoints, database layers, services, and startup logic.

- `api/`  
  RESTful endpoint definitions (e.g., `cityRouter.py`, `weatherRouter.py`)

- `core/`  
  Application-wide configuration and startup logic (e.g., `config.py`)

- `db/`  
  - `models/` – SQLModel entity classes  
  - `repositories/` – Data access abstraction layer

- `exceptions/`  
  Custom exceptions used across services

- `externals/`  
  Integration logic for third-party APIs (e.g., weather)

- `schemas/`  
  Pydantic models for request/response validation

- `services/`  
  Core business logic; one folder per microservice (e.g., `sunpot/`, `loader/`)

  Each service contains:
  - `README.md` – Functional and architectural overview  
  - `Dockerfile` – Standalone build instructions for the service

- `main.py`  
  Application entry point

## Containerized Service Definitions (`dockers/`)

Contains Docker Compose orchestration logic that brings together all services for development and testing.

- `loader/`  
  - Generates `docker-compose.yml` dynamically via `generate-compose.py`, based on `configs/config-service.yml`.  
  - Includes a `README.md` explaining the workflow and how service dependencies and health checks are coordinated.

- `services/`  
  - Contains individual service definitions (YAML fragments) used by the dynamic `generate-compose.py` script to assemble the final `docker-compose.yml`.  
  - Each file defines image, ports, volumes, environment, and health checks for services like CityDB, TimescaleDB, pgAdmin, Jupyter, and server-lists.  
  - These services are conditionally included based on their status in `configs/config-service.yml`.

- `sunpot/`  
  - Pipeline for solar potential analysis using CityDB v4 and Sunpot-Core.  
  - Includes Compose configuration for running Sunpot Core, Texture, Exporter, and Importer.  
  - `README.md` explains the workflow and how data flows from CityDB v4 to v5.

## Configuration Files (`configs/`)

Central config folder controlling service composition and runtime parameters.

- `config-service.yml` defines which services are active, exposed ports, credentials, etc.
- Service-specific config templates for loader, Sunpot, database credentials, etc.
- Referenced by `generate-compose.py` and service entry points.

## Test Suite (`tests/`)

Automated testing organized by scope.

- `unit/` – Tests for isolated modules (e.g., services, schemas)
- `integration/` – Tests that require communication between modules (e.g., DB ↔ API)
- `e2e/` – Full application flow simulation
- `conftest.py` – Shared fixtures and setup for Pytest-based testing
