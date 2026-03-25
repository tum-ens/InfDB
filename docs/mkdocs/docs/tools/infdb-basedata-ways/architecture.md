# Architecture

The architecture of the `infDB-basedata-ways` tool is based on the InfDB Dev Container template as described in the [Tool Template](../dev-container/index.md). The tool is implemented in Python and utilizes the `pyinfdb` package for interaction with InfDB. The database operations are executed using SQL queries.

!!! note "Remark"
    The architecture follows the InfDB Dev Container template. For detailed structure and dependencies, see the [Tool Template](../dev-container/index.md) section.

## Overview

The `infDB-basedata-ways` tool transforms raw ways-related input data into structured road network tables for downstream tools and analyses. The processing is executed through Python-based orchestration and SQL-based transformation steps in InfDB.

### Input Tables

The tool reads its source data from existing input tables:

- `opendata.basemap_verkehrslinie`
- `basedata.buildings`

### Intermediate Tables

During processing, the tool creates and updates temporary or intermediate tables used in the transformation workflow:

- `ways_tem`
- `ways_tem_connection`
- `connection_lines_tem`

### Output Tables

The tool writes the processed results into global output tables:

- `basedata.ways_per_junction`
- `basedata.nodes_per_junction`
- `basedata.ways_per_connection`
- `basedata.nodes_per_connection`
- `basedata.connection_lines`

## Functions

The main logic of the tool is implemented through SQL scripts and database functions. These components support assignment updates, segmentation, splitting operations, and connection generation.

#### `update_assigned_way_id`

Updates `buildings.assigned_way_id` based on a mapping table or nearest suitable way.

#### `insert_way_segment`

Inserts a generated way segment into the corresponding temporary table.

#### `split_way_at_connection_points`

Splits a way geometry into multiple segments at connection points.

#### `generate_building_way_connection_candidates`

Generates temporary connection candidates between buildings and assigned ways.

#### `update_assigned_way_id_after_merge`

Updates `buildings.assigned_way_id` after way-merging operations.

## Processing Steps

The SQL-based processing is organized into multiple sequential scripts. These scripts cover initialization, filtering, assignment, merging, segmentation, connection generation, and final insertion into output tables.

### SQL Scripts

- `create_temp_table.sql`  
  Creates the temporary working tables `ways_tem` and `connection_lines_tem` from the input ways data restricted to the selected AGS. It keeps one valid `LINESTRING` per source feature, adds additional columns needed in later processing steps, and creates indexes for efficient spatial and key-based operations.
- `initialization.sql`  
  Creates shared database functions and global output tables required for the processing workflow. It also ensures that parallel workers can initialize these resources safely without conflicts.
- `filter_by_class.sql`  
  Applies optional filtering rules to `ways_tem` based on configured `klasse` and `objektart` values. Rows that do not match the allowed filter conditions are removed from further processing.
- `01_a_building_address.sql`
- `01_b_assign_buildings_to_ways.sql`
- `02_a_merge_candidates.sql`
- `02_b_merge_chain.sql`
- `02_c_merge_ways.sql`
- `04_filter_isolated_loop_short.sql`
- `05_segment_intersecting_ways.sql`
- `06_generate_building_to_way_connections`
- `08_assign_postcodes.sql`
- `09_insert_temp_tables.sql`
- `10_insert_nodes.sql`