-- Summary: Calculates the number of households for residential buildings.
-- It derives this count from the estimated number of occupants and the average
-- household size from the corresponding grid cell, using nearest neighbor logic
-- for missing data.

-- Step 1: Create temp table linking buildings to avg household size grid
DROP TABLE IF EXISTS temp_building_hh_grid;
CREATE TEMP TABLE temp_building_hh_grid AS
SELECT b.id AS building_id,
       b.occupants,
       d.id as haushaltsgroesse_id,
       d.durchschnhhgroesse
FROM temp_buildings b
         JOIN temp_buildings_grid_100m d
             ON d.geom && b.geom AND
             ST_Contains(d.geom, ST_Centroid(b.geom))
WHERE b.occupants IS NOT NULL
  AND b.building_use = 'Residential'; -- already ensured by above clause

CREATE INDEX ON temp_building_hh_grid (building_id);

-- Step 2: Compute households per building
DROP TABLE IF EXISTS temp_building_households;
CREATE TEMP TABLE temp_building_households AS
SELECT building_id,
       GREATEST(ROUND(occupants / durchschnhhgroesse)::int, 1) AS estimated_households
FROM temp_building_hh_grid;

CREATE INDEX ON temp_building_households (building_id);

-- Step 3: Update original building table
UPDATE temp_buildings b
SET households = bh.estimated_households
FROM temp_building_households bh
WHERE b.id = bh.building_id;

-- Handle buildings without occupants using nearest neighbor
-- Step 4: Find nearest grid cell with occupancy data for each unassigned building
DROP TABLE IF EXISTS temp_nearest_grid_households;

CREATE TEMP TABLE temp_nearest_grid_households AS
SELECT
    b.id AS building_id,
    -- (bo.weight / bo.total_weight) * nearest.nearest_einwohner * (bo.total_weight / cw.total_weight) as assigned_occupants, -- ratio of building weight * closest occupancy count * ratio of total weights
    GREATEST(ROUND((bo.weight / cw.total_weight) * nearest.nearest_einwohner)::int, 1) as assigned_occupants
FROM temp_buildings b
CROSS JOIN LATERAL (
    SELECT g.id as bevoelkerungszahl_id,
           g.einwohner as nearest_einwohner
    FROM temp_buildings_grid_100m g
    WHERE g.id IS NOT NULL
      AND g.einwohner IS NOT NULL
    ORDER BY g.geom <-> ST_Centroid(b.geom)
    LIMIT 1
) nearest
JOIN temp_building_occupants bo ON b.id = bo.building_id
JOIN temp_cell_weights cw ON nearest.bevoelkerungszahl_id = cw.bevoelkerungszahl_id
WHERE b.occupants IS NULL
  AND b.building_use = 'Residential';

-- release memory
DROP TABLE IF EXISTS temp_building_hh_grid;
DROP TABLE IF EXISTS temp_building_households;
DROP TABLE IF EXISTS temp_nearest_grid_households;

-- from 09_fill_occupants.sql
DROP TABLE IF EXISTS temp_cell_weights;
DROP TABLE IF EXISTS temp_building_occupants;
