# InfDB Architecture Overview

This folder documents how InfDB is structured and how it works behind the scenes. It describes the system’s core components, data flow, and optional services that support advanced use cases like solar potential estimation.

## Purpose

The `architecture/` folder helps developers, analysts, and maintainers understand the internal structure and design decisions of InfDB. It outlines how different layers interact, how data is managed, and how additional services like solar simulation are integrated into the platform.

## Contents

- [**System Overview**](SYSTEM_OVERVIEW.md)  
  Describes the high-level architecture of InfDB, including the layered design (database, API, services, models) and how geospatial and time-series data are combined using raster-based resolution. It also covers key technologies such as PostgreSQL, 3DCityDB, TimescaleDB, and FastAPI.

- [**Data Loader**](DATA_LOADER.md)  
  Explains how infrastructure and datasets are configured and provisioned through a modular, Docker-based system. Includes architecture for the loader, how datasets are defined via configuration, and how new sources can be added through modular Python scripts.

- [**Solar Potential**](SOLAR_POTENTIAL.md)  
  Documents the optional solar simulation workflow powered by SunPot. Explains how LOD2 data is processed using CityDB v4, how results are migrated to CityDB v5, and how configuration files coordinate the process across multiple containers.

## Notes

- Each service runs as part of a Docker Compose stack and communicates through a shared virtual network.
- All data sources are defined declaratively using YAML configuration files.
- Each project (identified by a base name) maintains isolated folders and data pipelines for reproducibility and modularity.
- The architecture is extensible, allowing new datasets and services to be added with minimal effort.

For setup instructions, refer to the [development guides](../development/).
