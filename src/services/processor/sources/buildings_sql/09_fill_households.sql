-- fill households
-- Step 1: Create temp table linking buildings to avg household size grid
DROP TABLE IF EXISTS temp_building_hh_grid;
CREATE TEMP TABLE temp_building_hh_grid AS
SELECT b.id AS building_id,
       b.occupants,
       d.id as haushaltsgroesse_id,
       d.durchschnhhgroesse
FROM pylovo_input.buildings b
         JOIN opendata.cns22_100m_durchschn_haushaltsgroesse d
              ON ST_Contains(ST_Transform(d.geometry, 3035), ST_Centroid(b.geom))
WHERE b.occupants IS NOT NULL
  AND b.building_use = 'Residential'; -- already ensured by above clause

SELECT * FROM temp_building_hh_grid;

-- Step 2: Compute households per building
DROP TABLE IF EXISTS temp_building_households;
CREATE TEMP TABLE temp_building_households AS
SELECT building_id,
       GREATEST(ROUND(occupants / durchschnhhgroesse)::int, 1) AS estimated_households
FROM temp_building_hh_grid;

-- Step 3: Update original building table
UPDATE pylovo_input.buildings b
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
FROM pylovo_input.buildings b
CROSS JOIN LATERAL (
    SELECT g.id as bevoelkerungszahl_id,
           g.einwohner as nearest_einwohner
    FROM opendata.cns22_100m_bevoelkerungszahl g
    WHERE g.gitter_id_100m IS NOT NULL
      AND g.einwohner IS NOT NULL
    ORDER BY ST_Transform(g.geometry, 3035) <-> ST_Centroid(b.geom)
    LIMIT 1
) nearest
JOIN temp_building_occupants bo ON b.id = bo.building_id
JOIN temp_cell_weights cw ON nearest.bevoelkerungszahl_id = cw.bevoelkerungszahl_id
WHERE b.occupants IS NULL AND b.building_use = 'Residential';
