
# Solar Potential Calculations

InfDB includes a dedicated workflow for **solar potential estimation** on LOD2 data. This feature calculates how much solar energy each roof surface could receive, which is useful for urban energy modeling, rooftop PV planning, or sustainability analysis.

This module is **optional**, and can be enabled once the main infrastructure has been provisioned using the Data Loader.

## Purpose and Overview

The solar simulation pipeline is based on the **SunPot** toolset, which performs irradiance computations on 3D building geometries. It integrates with InfDB by processing LOD2 building models and storing results in CityDB schemas for further analysis and visualization.

## Architectural Setup

Unlike the main InfDB system, which uses **CityDB v5** by default, the **solar potential service operates on CityDB v4**. This is due to compatibility constraints of the current SunPot implementation, which only supports v4-style schemas.

The architectural flow includes both **CityDB v4 and v5**:

1. **LOD2 geometry is imported into CityDB v4**  
   This is done using a containerized Importer/Exporter tool.

2. **Solar simulations are executed on the v4 instance**  
   The core SunPot service performs irradiance estimation and writes results into a new schema called `sunpot`.

3. **Simulation results are exported as CSVs**  
   The `sunpot` schema is transformed into flat files suitable for cross-version migration.

4. **CityDB v5 imports those results**  
   A custom migration tool under `src/services/sunpot/` loads the data into the active v5 database.

This allows the simulation to run in its native (v4-compatible) environment while still making results available to the rest of InfDB.

## Configuration-Driven Integration

The solar pipeline reads configuration values from multiple files to ensure all database and path settings are consistent:

- **`configs/config-sunpot.yml`**  
  Defines connection settings for CityDB v4 (host, user, password, database name, EPSG).

- **`configs/config.yml`**  
  Provides project-specific paths (e.g., base directory, output folder for solar CSVs).

- **`configs/config-loader.yml`**  
  Supplies LOD2 dataset paths, including where the input GML files are stored.

From these configurations, the system determines:

- Where to read input geometry
- Where to store simulation results
- How to route data between database versions

## File and Folder Structure

The solar pipeline works within the same `infdb-data/<project_name>/` folder hierarchy used by the rest of InfDB:

- **LOD2 Input Geometry**  
  Comes from the existing processed folder (e.g., `infdb-data/sonthofen/lod2/`)

- **Simulation Output (SunPot CSVs)**  
  Written to a dedicated directory (e.g., `infdb-data/sunset/`) for clean separation

Each dataset's outputs are scoped to the current project using the `base_name`, ensuring repeatable and isolated runs.

## Extensibility and Isolation

Although solar potential calculations are currently limited to CityDB v4 due to tool compatibility, the pipeline is structured to allow:

- Updating the export/import process if schema versions change
- Running simulations independently of the main loader process

Because everything is defined via configuration and isolated per project, this feature can be safely enabled or skipped depending on your specific use case.

## Summary

- The solar potential module is an **optional one-time pipeline** for running SunPot simulations.
- It operates on **CityDB v4**, then migrates results to **CityDB v5** using an internal export-import flow.
- The pipeline is fully **containerized**, **configuration-driven**, and **project-scoped**.
- Results are stored in a standardized location and format, making them available for downstream energy analysis.

For setup and usage, refer to the solar pipeline guide under `development/solar_pipeline/`.
