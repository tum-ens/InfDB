# Architecture

The architecture of the `InfDB-basedata-buildings` tool is based on the InfDB Dev Container template as described in the [Tool Template](../dev-container/index.md). The tool is implemented in Python and utilizes the `pyinfdb` package for interaction with InfDB. The database operations are executed using SQL queries.

!!! note "Remark"
    The architecture follows the InfDB Dev Container template. For detailed structure and dependencies, see the [Tool Template](../dev-container/index.md) section.

## Overview
The infdb-basedata-buildings tool integrates 3D building data, census statistics at multiple spatial scales, and geographical weather data. It generates building-specific information and links local weather conditions to each building’s location.

Processing is carried out through a combination of Python-based orchestration and SQL-based transformation steps within infdb.

## Processing Steps
The SQL-based workflow is organized into a sequence of scripts. These scripts handle initialization, data assignment, processing and recalibration of variables, and the mapping of weather conditions to individual buildings.

#### 1. `00_initialization.sql` 
Responsible for creating all shared prerequisites (helper functions & tables) for basedata-buildings tool, as well as for creating the output schema (if it is already not created). 
It additionally uses an advisory lock to coordinate the parallel processing of multiple AGS safely.

#### 2. `01_create_temp_tables.sql` 
Creates temporary, per-session tables with the same structure as the global tables in the output schema, to isolate each run from the global tables during processing. These temporary tables are deleted at a later step.

#### 3. `02_fill_id_object_id_building_use.sql` 
This loads and sychronizes the temp buildings table, with buildings information and identifiers from the source building data (LOD2). 

#### 4. `03_fill_height.sql` 
Fills the building height column in the temp buildings table, using data from LOD2. It also removes buildings with invalid or improbable heights (very small buildings).

#### 5. `04_fill_floor_area_geom.sql` 
Populates the gemoetry, centroid and floor area fields in the buildings table from LOD2 data. Additionally, it removes invalid buildings with very small areas.

#### 6. `05_fill_floor_number.sql` 
Assigns the floor numbers for buildings, using the storey values from LOD2 when available. If missing, values are derived using average floor heights and the total building height, or relying on standard fallback values.

#### 7. `06_prepare_grid.sql` 
Builds the buildings_grid tables by spatially joining the grid cells with the centroids of buildings. These building_grid tables are then enriched with respective information from Zensus on population, construction years, household sizes, and building types.

#### 8. `07_fill_occupants.sql` 
Estimates the residential occupants per building proportionally based on the building volumes. In case of insufficient grid cell data, buildings are assigned occupants based on information from the nearest populated grid cells.

#### 9. `08_fill_households.sql` 
Derives the number of households for each building, based on its number of occupants and the average household size for that grid cell. Utilizes information from neighbouring cells in case of missing data.

#### 10. `09_fill_construction_year.sq` 
Assigns a construction year period for each building, using a random weighted assignment derived from the construction year information from Zensus.

#### 11. `10_assign_postcode_to_buildings.sql`
Assigns postal code information to buildings, by performing a spatial join between building centroids and a table containing postal code gemoetries.

#### 12. `11_create_building_to_grid.sql`
It creates a table (bld2ts) linking buildings to their relevant weather data, by selecting the nearest OpenMeteo time-series metadata for each building.

#### 13. `12_create_touching_buildings_temp_tables.sql`
It creates temporary tables identifying touching residential buildings. This is necessary to compute adjacency relationships and neighbouring counts, crucial for determining building types at a later stage.

#### 14. `13_a_fill_buildings_type_AB.sql, 13_b_fill_building_type_SFH.sql, 13_c_fill_building_type_TH.sql, 13_d_fill_building_type_MFH.sql `
Identify and classify residential buildings as one of following four type - AB, SFH, TH and MFH- based on a combination of building attributes (No. of floors, area, neighbours) and on graph-based analysis.

#### 15. `14_fill_building_type_postprocessing.sql `
Applies postprocessing to building types, assigning default types to remaining unlabeled buildings, and rebalancing the building type distributions to align them with grid cell statistics from Zensus.

#### 16. `15_flush_temp_tables.sql `
Pushes the temp table data into the final output tables, either inserting or upserting the values in those tables. At the end, the temp tables are also deleted.

