# Development Folder

This folder contains guides, best practices, and setup instructions for developing and running InfDB locally. It is organized into two subfolders:

## Purpose

The `development/` folder is meant to **guide contributors and maintainers**. Whether you're setting up the system, running pipelines, or contributing code, this folder provides all necessary instructions in one place.


## `api/` — API Development Guide

This folder includes documentation for working with the FastAPI-based backend:

- **`overview.md`**  
  Introduction to the API structure, routes, and how endpoints are organized.

- **`usage.md`**  
  Explains how to interact with the API (e.g., via Swagger UI, curl, or frontend clients).

- **`error_handling_and_best_practises.md`**  
  Covers recommended practices for error handling, response structure, and validation using FastAPI and Pydantic.


## `get_started/` — Local Setup & Troubleshooting

This folder helps new developers set up and run InfDB on their local machines. It includes practical guides and workflows.

- **`ide_config.md`**  
  Recommended IDE extensions, linters, and configurations for working on InfDB.

- **`local_setup.md`**  
  Step-by-step instructions to spin up the entire system using Docker.

- **`solar_pipeline.md`**  
  Explains how to run the solar potential analysis pipeline using SunPot and 3DCityDB.

- **`testing.md`**  
  Describes how to run unit, integration, and end-to-end tests.

- **`troubleshooting.md`**  
  Common problems during development and how to fix them.

- **`workflow.md`**  
  Developer workflow overview including Git branching, code formatting, and how to contribute effectively.


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
