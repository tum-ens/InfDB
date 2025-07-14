-- fill construction_year
-- Step 1: Create a table with joined buildings and grid cells
DROP TABLE IF EXISTS temp_building_with_grid_year;
CREATE TEMP TABLE temp_building_with_grid_year AS
SELECT b.id   AS building_id,
       b.geom AS building_geom,
       g.*
FROM pylovo_input.buildings b
         JOIN opendata.cns22_100m_gebaeude_nach_baujahr_in_mikrozensus_klassen g
             ON ST_Contains(ST_Transform(g.geometry, 3035), ST_Centroid(b.geom))
WHERE g.gitter_id_100m IS NOT NULL;


-- Step 2: Assign construction year using weighted random distribution
-- Note: This version uses a WITH clause to prepare weights and cumulative ranges.
--       Then assigns a construction_year based on a random number weighted by those counts.
UPDATE pylovo_input.buildings b
SET construction_year = sub.assigned_year
FROM (SELECT building_id,
             pylovo_input.assign_weighted_year(
                     vor1919,
                     a1919bis1948,
                     a1949bis1978,
                     a1979bis1990,
                     a1991bis2000,
                     a2001bis2010,
                     a2011bis2019,
                     a2020undspaeter,
                     r)
                 AS assigned_year
      FROM (SELECT building_id,
                   vor1919,
                   a1919bis1948,
                   a1949bis1978,
                   a1979bis1990,
                   a1991bis2000,
                   a2001bis2010,
                   a2011bis2019,
                   a2020undspaeter,
                   random() AS r
            FROM temp_building_with_grid_year) year_probs) sub
WHERE b.id = sub.building_id;

-- Handle buildings without construction_year using nearest neighbor
-- Step 3: Find nearest grid cell with construction year data for each unassigned building
DROP TABLE IF EXISTS temp_nearest_grid_year;
CREATE TEMP TABLE temp_nearest_grid_year AS
SELECT
    b.id AS building_id,
    nearest.*
FROM pylovo_input.buildings b
CROSS JOIN LATERAL (
    SELECT g.gitter_id_100m,
           g.vor1919,
           g.a1919bis1948,
           g.a1949bis1978,
           g.a1979bis1990,
           g.a1991bis2000,
           g.a2001bis2010,
           g.a2011bis2019,
           g.a2020undspaeter
    FROM opendata.cns22_100m_gebaeude_nach_baujahr_in_mikrozensus_klassen g
    WHERE g.gitter_id_100m IS NOT NULL
      AND (COALESCE(g.vor1919, 0) + COALESCE(g.a1919bis1948, 0) +
           COALESCE(g.a1949bis1978, 0) + COALESCE(g.a1979bis1990, 0) +
           COALESCE(g.a1991bis2000, 0) + COALESCE(g.a2001bis2010, 0) +
           COALESCE(g.a2011bis2019, 0) + COALESCE(g.a2020undspaeter, 0)) > 0
    ORDER BY ST_Transform(g.geometry, 3035) <-> ST_Centroid(b.geom)
    LIMIT 1
) nearest
WHERE b.construction_year IS NULL;

-- Step 4: Assign construction year using the same weighted random logic
UPDATE pylovo_input.buildings b
SET construction_year = sub.assigned_year
FROM (SELECT building_id,
             pylovo_input.assign_weighted_year(
                     vor1919,
                     a1919bis1948,
                     a1949bis1978,
                     a1979bis1990,
                     a1991bis2000,
                     a2001bis2010,
                     a2011bis2019,
                     a2020undspaeter,
                     r)
                 AS assigned_year
      FROM (SELECT building_id,
                   vor1919,
                   a1919bis1948,
                   a1949bis1978,
                   a1979bis1990,
                   a1991bis2000,
                   a2001bis2010,
                   a2011bis2019,
                   a2020undspaeter,
                   random() AS r
            FROM temp_nearest_grid_year) year_probs) sub
WHERE b.id = sub.building_id
  AND b.construction_year IS NULL;