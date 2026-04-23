-- Summary: Estimates the number of occupants for residential buildings.
-- It distributes population data from zensus grid cells to buildings proportionally
-- based on building volume. Buildings without direct grid data are assigned
-- occupants using the nearest populated grid cell.

-- Step 1: Create temp table for buildings with cell and weight
DROP TABLE IF EXISTS temp_building_weights;
CREATE TEMP TABLE temp_building_weights AS
SELECT b.id                    AS building_id,
       b.height * b.floor_area AS weight,
       g.id                    as bevoelkerungszahl_id,
       g.einwohner
FROM temp_buildings b
    JOIN temp_buildings_grid_100m g
    ON ST_Contains(g.geom, b.centroid)
WHERE b.building_use = 'Residential'
  AND b.centroid && g.geom;  -- Bounding box filter before spatial query

CREATE INDEX ON temp_building_weights (bevoelkerungszahl_id);

-- Step 2: Create temp table for total weights per grid cell
DROP TABLE IF EXISTS temp_cell_weights;
CREATE TEMP TABLE temp_cell_weights AS
SELECT bevoelkerungszahl_id,
       SUM(weight) AS total_weight
FROM temp_building_weights
GROUP BY bevoelkerungszahl_id;

CREATE INDEX ON temp_cell_weights (bevoelkerungszahl_id);


-- Step 3: Assign occupants proportionally to each building
DROP TABLE IF EXISTS temp_building_occupants;
CREATE TEMP TABLE temp_building_occupants AS
SELECT bw.building_id,
       bw.weight,
       bw.bevoelkerungszahl_id,
       bw.einwohner,
       cw.total_weight,
       CASE
           WHEN cw.total_weight > 0 THEN GREATEST(ROUND((bw.weight / cw.total_weight) * bw.einwohner)::int, 1)
           ELSE 0
           END AS assigned_occupants
FROM temp_building_weights bw
         JOIN temp_cell_weights cw
              ON bw.bevoelkerungszahl_id = cw.bevoelkerungszahl_id;

-- Step 4: Update the original building table
UPDATE temp_buildings b
SET occupants = bo.assigned_occupants
FROM temp_building_occupants bo
WHERE b.id = bo.building_id;

-- Handle buildings without occupants using nearest neighbor
-- Step 5: Find nearest grid cell with occupancy data for each unassigned building
DROP TABLE IF EXISTS temp_nearest_grid_occupants;
CREATE TEMP TABLE temp_nearest_grid_occupants AS
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
    ORDER BY g.geom <-> b.centroid
    LIMIT 1
) nearest
JOIN temp_building_occupants bo ON b.id = bo.building_id
JOIN temp_cell_weights cw ON nearest.bevoelkerungszahl_id = cw.bevoelkerungszahl_id
WHERE b.occupants IS NULL AND b.building_use = 'Residential';

-- Step 6: Update the original building table with the nearest estimations
UPDATE temp_buildings b
SET occupants = ngo.assigned_occupants
FROM temp_nearest_grid_occupants ngo
WHERE b.id = ngo.building_id;

-- release memory
DROP TABLE IF EXISTS temp_building_weights;
DROP TABLE IF EXISTS temp_nearest_grid_occupants;
