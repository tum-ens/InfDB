# Data Loader

In addition to the core architectural components like 3DCityDB and TimescaleDB, InfDB includes a major service that enables automated data ingestion and domain-specific analysis workflows. The service support modular, extensible operations through containerized pipelines.

The **Data Loader** is a Docker-based orchestration system that automates the setup of InfDB services and handles the ingestion of external datasets. It deploys containers like **CityDB**, **TimescaleDB**, and **pgAdmin**, performs health checks, and prepares the environment for data loading.

## Purpose and Function

The loader is designed to:

- Launch required services like **3DCityDB**, **TimescaleDB**, and **pgAdmin** using Docker Compose
- Define infrastructure and dataset-specific configurations via YAML files
- Process and load external datasets into the appropriate database schemas
- Isolate each project’s data using dynamic path resolution based on the project name (referred to as `base_name`)

## Configuration-Driven Setup

The loader relies on the following key configuration files:

- **`configs/config-service.yml`**  
  Defines which services are active (e.g. CityDB, TimescaleDB), their ports, credentials, and volume paths.

- **`configs/config-loader.yml`**  
  Describes each dataset to be loaded: including download paths, processing stages, file structure, and the schema it should be written to.

- **`.env` file**  
  Defines environment variables consumed by services.

- **`docker-compose.yml`**  
  Automatically generated based on active services and their configurations.

All active services are defined modularly in the `dockers/` folder as individual YAML fragments. These fragments are composed together into a single `docker-compose.yml` using the `generate-compose.py` script.

## Supported Datasets

InfDB currently supports a rich set of external datasets, all configured via `config-loader.yml`. These include:

- **LOD2 Building Models** (e.g., [Bavarian Geodata](https://geodaten.bayern.de))
- **Street Networks** (e.g., [BaseMap Open Data](https://basemap.de/open-data/))
- **Administrative Boundaries** (e.g., [BKG](https://gdz.bkg.bund.de))
- **Postal Code Areas** (e.g., [PLZ GeoJSON](https://www.suche-postleitzahl.org))
- **Zensus 2022** grid-based statistical data

Each source is declared with:
- A name (e.g., `lod2`, `basemap`, `zensus_2022`)
- A schema (`citydb`, `opendata`, etc.)
- Resolutions (for gridded data)
- Download URL(s)
- Internal file structure and storage paths

## Folder and Data Organization

To keep data modular and reusable across multiple regions or experiments, the loader follows a **base name strategy**:

- Each project is given a unique `base_name` (e.g., `sonthofen`)
- All input and processed data is stored under `infdb-data/<base_name>/`
- A separate `opendata/` folder is used to store raw shared datasets

This results in a clean structure like:

infdb-data/
├── opendata/ # Raw downloads shared across projects
├── sonthofen/ # Project-specific processed outputs
│ ├── zensus_2022/
│ ├── lod2/
│ ├── basemap/
│ └── ...

Each dataset manages its own folder under the project path and keeps processed versions of its inputs and any transformation results.

## Data Flow into the Database

Once datasets are registered and configured:

1. The loader reads all paths and metadata from `config-loader.yml`
2. It invokes corresponding **loader services** under `src/services/`
3. These services read and process the input files, apply validations or conversions and then write to 3DCityDB.

All services are containerized and interact over a shared Docker network, ensuring consistent communication and isolation from the host environment.

## #Extending the system with a new dataset involves the following steps:

1. **Create a new entry under `sources:` in `config-loader.yml`**  
   Define the dataset name, status (`active`), target schema, file paths, and any additional metadata like resolution or layer names.

2. **Provide the correct download URL and folder structure**  
   This includes raw download location, unzip directory, and processed output path. These paths ensure consistency across all data handling steps.

3. **Implement a Python loader script**  
   Each dataset must have a dedicated Python script under `src/services/loader/sources/`. This script should handle all steps for that dataset:
   - Downloading
   - Unpacking
   - Processing
   - Loading into the database

   The script should follow the modular pattern used by existing sources for reusability and consistency.

4. **Register the script for automatic execution**  
   The new loader must be added to the loader service’s startup routine so that it is picked up automatically when the loader runs. This ensures the dataset is processed without manual intervention.

This design allows InfDB to support a wide variety of datasets while keeping ingestion logic modular and maintainable.

### Summary

- The **Data Loader** automates both service orchestration and dataset ingestion using declarative configs.
- Datasets are modular, independently defined, and project-aware.
- All services and data sources run in containers and are dynamically composed.
- This design ensures InfDB is reproducible, scalable, and easy to extend with minimal manual setup.

For step-by-step usage, refer to the [Local Setup Guide](../development/get_started/local_setup.md).
