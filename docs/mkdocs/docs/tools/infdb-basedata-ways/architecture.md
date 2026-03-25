# Architecture

The architecture of the `infDB-basedata-ways` tool is based on the InfDB Dev Container template as described in the [Tool Template](../dev-container/index.md). The tool is implemented in Python and utilizes the `pyinfdb` package for interaction with InfDB. The database operations are executed using SQL queries.

!!! note "Remark"
    The architecture follows the InfDB Dev Container template. For detailed structure and dependencies, see the [Tool Template](../dev-container/index.md) section.

## Overview

The `infDB-basedata-ways` tool transforms raw ways-related input data into structured road network tables for downstream tools and analyses. The processing is executed through Python-based orchestration and SQL-based transformation steps in InfDB.

### Input Tables

The tool reads its source data from existing input tables:

- `opendata.basemap_verkehrslinie`: Stores the raw way geometries and related source attributes used as the basis for road network generation.
- `basedata.buildings`: Stores the building geometries and attributes for buildings that are assigned and connected to suitable ways during processing.

### Intermediate Tables

During processing, the tool creates and updates temporary or intermediate tables used in the transformation workflow:

- `ways_tem`: Temporary working table used to process and segment ways for the generation of `basedata.ways_per_junction`.
- `ways_tem_connection`: Temporary working table used to process ways for the generation of `basedata.ways_per_connection`. In this table, ways are additionally split at building-to-way connection points.
- `connection_lines_tem`: Temporary table used to store the generated building-to-way connection lines during processing.

### Output Tables

The tool writes the processed results into global output tables:

- `basedata.ways_per_connection`: Stores the final way network designed for the Pylovo tool. In this network, ways are additionally segmented at building-to-way connection points.
- `basedata.nodes_per_connection`: Stores the nodes of the way network contained in `basedata.ways_per_connection`.
- `basedata.ways_per_junction`: Stores the final way network designed for the linear heat density tool. In this network, ways are segmented at way junctions but not additionally at building-to-way connection points.
- `basedata.nodes_per_junction`: Stores the nodes of the way network contained in `basedata.ways_per_junction`.
- `basedata.connection_lines`: Stores the generated connection lines between buildings and their assigned ways.

## Functions

The main logic of the tool is implemented through SQL scripts and database functions. These components support assignment updates, segmentation, splitting operations, and connection generation.


#### `insert_way_segment`

Inserts a generated way segment into the corresponding temporary table.

#### `split_way_at_connection_points`

Splits a way geometry into multiple segments at connection points.

#### `generate_building_way_connection_candidates`

Generates temporary connection candidates between buildings and assigned ways.

#### `update_assigned_way_id_after_merge`

Updates `buildings.assigned_way_id` after way-merging operations.

#### `update_assigned_way_id`

Updates `buildings.assigned_way_id` based on a mapping table or nearest suitable way.

## Processing Steps

The SQL-based processing is organized into multiple sequential scripts. These scripts cover initialization, filtering, assignment, merging, segmentation, connection generation, and final insertion into output tables.

#### 1. `create_temp_table.sql` 
  Creates the temporary working tables `ways_tem` and `connection_lines_tem` from the input ways data restricted to the selected AGS. It keeps one valid `LINESTRING` per source feature, adds additional columns needed in later processing steps, and creates indexes for efficient spatial and key-based operations.
#### 2. `initialization.sql`  
  Creates shared database functions and global output tables required for the processing workflow. It also ensures that parallel workers can initialize these resources safely without conflicts.
#### 3. `filter_by_class.sql`  
  Applies optional filtering rules to `ways_tem` based on configured `klasse` and `objektart` values. Rows that do not match the allowed filter conditions are removed from further processing.
#### 4. `building_address.sql`  
  Matches buildings to nearby named ways based on their parsed street address and stores the result in `buildings.address_street_id`. If multiple matching ways exist, the nearest one is selected.
#### 5. `assign_buildings_to_ways.sql`  
  Assigns each building to a suitable way and writes the result to `buildings.assigned_way_id`. Depending on the configuration, it prefers a direct match via address information and otherwise falls back to the nearest suitable way.
#### 6. `merge_candidates.sql`  
  Creates temporary merge candidate data for `ways_tem` by analyzing neighbouring line endpoints within a distance tolerance. It identifies adjacent way segments and stores the required information for later way-merging steps.
#### 7. `merge_chain.sql`  
  Builds connected chains of mergeable ways based on the previously identified merge candidates. It groups linked way segments into connected components so they can be merged in later processing steps.
#### 8. `merge_ways.sql`  
  Merges connected way segments in `ways_tem` into single way geometries based on the previously generated chain candidates. It uses `update_assigned_way_id_after_merge` to update affected building-to-way assignments after the merge.
#### 9. `filter_isolated_loop_short.sql`  
  Filters selected ways from `ways_tem` by removing loops, isolated ways, and short segments depending on the configured rules. After filtering, it uses `update_assigned_way_id` to update affected building-to-way assignments and, where applicable, transfers the removed way length to a replacement way.
#### 10. `segment_intersecting_ways.sql`  
  Splits intersecting ways in `ways_tem` at their intersection points and reinserts the resulting segments. This step ensures that crossings are represented as separate connected way segments for later network generation.
#### 11. `generate_building_to_way_connection.sql`  
  Generates building-to-way connection lines and updates the related way attributes in `ways_tem`. It then creates `ways_tem_connection` as a copy of `ways_tem` and splits the affected ways at the building-to-way connection points only in `ways_tem_connection`.
#### 12. `assign_postcodes.sql`  
  Assigns postcode values to the generated temporary way and connection tables based on postcode polygon intersections. This ensures that the processed geometries can be linked to postcode-based downstream analyses.
#### 13. `insert_temp_tables.sql`  
  Inserts the final processed temporary way and connection data into the global output tables for the current AGS. Existing rows for the same AGS are replaced to keep the results idempotent.
#### 14. `insert_nodes.sql`  
  Creates node tables by clustering way endpoints and inserting the resulting junction points together with their related way IDs. It generates nodes for both `ways_per_junction` and `ways_per_connection`.