-- Summary: Assigns a construction year to each building based on census data
-- distributions. It uses a weighted random assignment derived from construction
-- year bands in the corresponding or nearest grid cell.
--
-- Reproducibility note: We do not use PostgreSQL's session-level random()
-- here because the same random stream can be consumed in different row orders.
-- Instead, each building gets a deterministic pseudo-random value derived from
-- its stable objectid and the configured seed.
-- Step 1: Create a table with joined buildings and grid cells
DROP TABLE IF EXISTS temp_building_with_grid_year;
CREATE TEMP TABLE temp_building_with_grid_year AS
SELECT b.id   AS building_id,
    b.objectid AS building_objectid,
       b.geom AS building_geom,
       g.*
FROM temp_buildings b
    JOIN temp_buildings_grid_100m g
    ON g.geom && b.centroid
        AND ST_Contains(g.geom, b.centroid)
WHERE g.id IS NOT NULL;

CREATE INDEX ON temp_building_with_grid_year(building_id);

-- Step 2: Assign construction year using weighted random distribution
-- Note: This version uses a WITH clause to prepare weights and cumulative ranges.
--       Then assigns a construction_year based on a random number weighted by those counts.
UPDATE temp_buildings b
SET construction_year = sub.assigned_year
FROM (SELECT building_id,
             {output_schema}.assign_weighted_year(
                     COALESCE(NULLIF(vor1919, 'NaN'::double precision), 0),
                     COALESCE(NULLIF(a1919bis1948, 'NaN'::double precision), 0),
                     COALESCE(NULLIF(a1949bis1978, 'NaN'::double precision), 0),
                     COALESCE(NULLIF(a1979bis1990, 'NaN'::double precision), 0),
                     COALESCE(NULLIF(a1991bis2000, 'NaN'::double precision), 0),
                     COALESCE(NULLIF(a2001bis2010, 'NaN'::double precision), 0),
                     COALESCE(NULLIF(a2011bis2019, 'NaN'::double precision), 0),
                     COALESCE(NULLIF(a2020undspaeter, 'NaN'::double precision), 0),
                     r)
                 AS assigned_year
      FROM (SELECT building_id,
                   building_objectid,
                   vor1919,
                   a1919bis1948,
                   a1949bis1978,
                   a1979bis1990,
                   a1991bis2000,
                   a2001bis2010,
                   a2011bis2019,
                   a2020undspaeter,
                   (
                       (
                           get_byte(decode(md5(format('%s:%s', '{random_seed}', building_objectid)), 'hex'), 0)::bigint * 16777216 +
                           get_byte(decode(md5(format('%s:%s', '{random_seed}', building_objectid)), 'hex'), 1)::bigint * 65536 +
                           get_byte(decode(md5(format('%s:%s', '{random_seed}', building_objectid)), 'hex'), 2)::bigint * 256 +
                           get_byte(decode(md5(format('%s:%s', '{random_seed}', building_objectid)), 'hex'), 3)::bigint
                       )::double precision / 4294967295.0
                   ) AS r
            FROM temp_building_with_grid_year) year_probs) sub
WHERE b.id = sub.building_id;


-- Handle buildings without construction_year using nearest neighbor
-- Step 3: Find nearest grid cell with construction year data for each unassigned building
DROP TABLE IF EXISTS temp_nearest_grid_year;
CREATE TEMP TABLE temp_nearest_grid_year AS
SELECT
    b.id AS building_id,
    b.objectid AS building_objectid,
    nearest.*
FROM temp_buildings b
CROSS JOIN LATERAL (
    SELECT g.id,
           g.vor1919,
           g.a1919bis1948,
           g.a1949bis1978,
           g.a1979bis1990,
           g.a1991bis2000,
           g.a2001bis2010,
           g.a2011bis2019,
           g.a2020undspaeter
    FROM temp_buildings_grid_100m g
    WHERE g.id IS NOT NULL
      AND (COALESCE(NULLIF(g.vor1919, 'NaN'::double precision), 0) +
           COALESCE(NULLIF(g.a1919bis1948, 'NaN'::double precision), 0) +
           COALESCE(NULLIF(g.a1949bis1978, 'NaN'::double precision), 0) +
           COALESCE(NULLIF(g.a1979bis1990, 'NaN'::double precision), 0) +
           COALESCE(NULLIF(g.a1991bis2000, 'NaN'::double precision), 0) +
           COALESCE(NULLIF(g.a2001bis2010, 'NaN'::double precision), 0) +
           COALESCE(NULLIF(g.a2011bis2019, 'NaN'::double precision), 0) +
           COALESCE(NULLIF(g.a2020undspaeter, 'NaN'::double precision), 0)) > 0
    ORDER BY g.geom <-> b.centroid 
    LIMIT 1
) nearest
WHERE b.construction_year IS NULL;

-- Step 4: Assign construction year using the same weighted random logic
UPDATE temp_buildings b
SET construction_year = sub.assigned_year
FROM (SELECT building_id,
             {output_schema}.assign_weighted_year(
                     COALESCE(NULLIF(vor1919, 'NaN'::double precision), 0),
                     COALESCE(NULLIF(a1919bis1948, 'NaN'::double precision), 0),
                     COALESCE(NULLIF(a1949bis1978, 'NaN'::double precision), 0),
                     COALESCE(NULLIF(a1979bis1990, 'NaN'::double precision), 0),
                     COALESCE(NULLIF(a1991bis2000, 'NaN'::double precision), 0),
                     COALESCE(NULLIF(a2001bis2010, 'NaN'::double precision), 0),
                     COALESCE(NULLIF(a2011bis2019, 'NaN'::double precision), 0),
                     COALESCE(NULLIF(a2020undspaeter, 'NaN'::double precision), 0),
                     r)
                 AS assigned_year
      FROM (SELECT building_id,
                   building_objectid,
                   vor1919,
                   a1919bis1948,
                   a1949bis1978,
                   a1979bis1990,
                   a1991bis2000,
                   a2001bis2010,
                   a2011bis2019,
                   a2020undspaeter,
                   (
                       (
                           get_byte(decode(md5(format('%s:%s', '{random_seed}', building_objectid)), 'hex'), 0)::bigint * 16777216 +
                           get_byte(decode(md5(format('%s:%s', '{random_seed}', building_objectid)), 'hex'), 1)::bigint * 65536 +
                           get_byte(decode(md5(format('%s:%s', '{random_seed}', building_objectid)), 'hex'), 2)::bigint * 256 +
                           get_byte(decode(md5(format('%s:%s', '{random_seed}', building_objectid)), 'hex'), 3)::bigint
                       )::double precision / 4294967295.0
                   ) AS r
            FROM temp_nearest_grid_year) year_probs) sub
WHERE b.id = sub.building_id
  AND b.construction_year IS NULL;


-- Step 5: Bundesland-level fallback for AGS where no census grid cell has
-- construction year data (e.g. Gemeindefreies Gebiet — uninhabited forest areas).
-- Steps 1-4 only search within the current AGS's grid cells; when the entire AGS
-- lacks census coverage, those steps leave construction_year NULL.
-- This fallback aggregates the construction year distribution across all census
-- grid cells in the same Bundesland (matched via the AGS prefix) and draws from
-- that state-wide distribution using the same deterministic random seed.
DO $$
DECLARE
    v_null_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_null_count
    FROM temp_buildings
    WHERE construction_year IS NULL;

    IF v_null_count = 0 THEN
        RETURN;
    END IF;

    RAISE NOTICE '[09_fill_construction_year] AGS {ags}: % buildings still without construction_year after nearest-neighbor fallback — applying Bundesland-level fallback (state prefix: %)',
        v_null_count, LEFT('{ags}', 2);

    UPDATE temp_buildings b
    SET construction_year = {output_schema}.assign_weighted_year(
            state_agg.s_vor1919,
            state_agg.s_a1919bis1948,
            state_agg.s_a1949bis1978,
            state_agg.s_a1979bis1990,
            state_agg.s_a1991bis2000,
            state_agg.s_a2001bis2010,
            state_agg.s_a2011bis2019,
            state_agg.s_a2020undspaeter,
            (
                get_byte(decode(md5(format('%s:%s', '{random_seed}', b.objectid)), 'hex'), 0)::bigint * 16777216 +
                get_byte(decode(md5(format('%s:%s', '{random_seed}', b.objectid)), 'hex'), 1)::bigint * 65536 +
                get_byte(decode(md5(format('%s:%s', '{random_seed}', b.objectid)), 'hex'), 2)::bigint * 256 +
                get_byte(decode(md5(format('%s:%s', '{random_seed}', b.objectid)), 'hex'), 3)::bigint
            )::double precision / 4294967295.0
        )
    FROM (
        SELECT
            SUM(COALESCE(z.vor1919, 0))            AS s_vor1919,
            SUM(COALESCE(z.a1919bis1948, 0))       AS s_a1919bis1948,
            SUM(COALESCE(z.a1949bis1978, 0))       AS s_a1949bis1978,
            SUM(COALESCE(z.a1979bis1990, 0))       AS s_a1979bis1990,
            SUM(COALESCE(z.a1991bis2000, 0))       AS s_a1991bis2000,
            SUM(COALESCE(z.a2001bis2010, 0))       AS s_a2001bis2010,
            SUM(COALESCE(z.a2011bis2019, 0))       AS s_a2011bis2019,
            SUM(COALESCE(z.a2020undspaeter, 0))    AS s_a2020undspaeter
        FROM {input_schema}.zensus_2022_100m_gebaeude_baujahr_mikrozensus z
        JOIN {input_schema}.bkg_vg5000_gem bkg
            ON bkg.ags LIKE LEFT('{ags}', 2) || '%%'
            AND ST_Intersects(z.geom, bkg.geom)
    ) state_agg
    WHERE b.construction_year IS NULL;
END $$;
