-- Create TEMP tables (per-container / per-AGS) with the same structure as global tables.
-- These tables live only for the current session/connection and won’t collide across containers.

CREATE TEMP TABLE IF NOT EXISTS temp_buildings
(LIKE {output_schema}.buildings INCLUDING ALL);

CREATE TEMP TABLE IF NOT EXISTS temp_buildings_grid_100m
(LIKE {output_schema}.buildings_grid_100m INCLUDING ALL);

CREATE TEMP TABLE IF NOT EXISTS temp_buildings_grid_1km
(LIKE {output_schema}.buildings_grid_1km INCLUDING ALL);

-- CREATE TEMP TABLE IF NOT EXISTS temp_bld2grid
-- (LIKE {output_schema}.bld2grid INCLUDING ALL);

CREATE TEMP TABLE IF NOT EXISTS temp_bld2ts
(LIKE {output_schema}.bld2ts INCLUDING ALL);

CREATE TEMP TABLE IF NOT EXISTS temp_grid_cells
(LIKE {input_schema}.grid_cells INCLUDING ALL);

CREATE TEMP TABLE IF NOT EXISTS temp_building_surface
(LIKE {output_schema}.building_surface_area INCLUDING ALL);