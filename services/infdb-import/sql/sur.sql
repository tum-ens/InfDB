CREATE OR REPLACE FUNCTION public.safe_area_fallback(geom geometry) 
RETURNS double precision AS $$
BEGIN
    -- ATTEMPT 1: Exact 3D calculation (scientifically correct)
    -- Attempts to decompose the polygon into triangles.
    RETURN GC_3DArea(ST_Tesselate(ST_MakeValid(geom)));

EXCEPTION WHEN OTHERS THEN
    -- EMERGENCY FALLBACK: If 3D crashes (InternalError), we use the 2D area.
    -- ST_Area(geom) ignores Z-values, but NEVER crashes.
    -- This is better than no value at all.
    RETURN 0;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

------------------------------------------------------
-- Create linking table between building and (sub)surfaces
------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS postgis_sfcgal;

CREATE SCHEMA IF NOT EXISTS tmp_bld;

-- 3. Temporary table: UNLOGGED is the key for speed
DROP TABLE IF EXISTS tmp_bld.{table_name}_ids;

-- We extract the ID hash directly for the join to save RAM
-- Use EXPLAIN ANALYZE to diagnose query performance
-- EXPLAIN ANALYZE
CREATE TABLE tmp_bld.{table_name}_ids AS
SELECT
    f.objectid as building_objectid,
    child ->> 'objectId' AS child_object_id_text,
    -- HASHING: Converts the 60-byte string into a 4-byte integer for the join
    hashtext(child ->> 'objectId') AS child_hash, 
    gd.id AS geometry_data_id,
    f.objectclass_id
FROM feature f
    JOIN geometry_data gd ON f.id = gd.feature_id
    CROSS JOIN LATERAL jsonb_array_elements(gd.geometry_properties -> 'children') AS child
WHERE f.objectclass_id IN (709, 710, 712, 901)
    AND (child ->> 'objectId') IS NOT NULL;

-- 4. Indexes: Only the necessary ones. Hash index for the join is no longer needed, 
-- since we already hashed. A B-tree on the integer hash is extremely fast.
CREATE INDEX IF NOT EXISTS idx_tmp_join_hash ON tmp_bld.{table_name}_ids (child_hash);
-- This index helps filter by objectclass in the join
CREATE INDEX IF NOT EXISTS idx_tmp_obj_class ON tmp_bld.{table_name}_ids (objectclass_id);


-------------------------------------------------------------
-- Create the final surface table with area and geometry
-------------------------------------------------------------

-- Analysis helps the query planner understand statistics for the join
ANALYZE tmp_bld.{table_name}_ids;

-- 5. Create the result table (Also UNLOGGED if it's only an intermediate step, 
-- otherwise keep LOGGED for data safety after import)
DROP TABLE IF EXISTS {output_schema}.{table_name} CASCADE;

-- EXPLAIN ANALYZE
CREATE TABLE {output_schema}.{table_name} AS
SELECT
    sid2.building_objectid,
    sid.objectclass_id,
    oc.classname,
    -- NULLIF prevents crashes on empty strings, just in case
    -- NULLIF(pd.val_string, '')::double precision AS area, 
    -- safe_area_fallback(gd.geometry) AS area,
    pd.val_string::double precision AS area,
    ST_Multi(gd.geometry) AS geom
FROM tmp_bld.{table_name}_ids sid
    -- Join on integer hash instead of string (massive speedup)
    JOIN tmp_bld.{table_name}_ids sid2 
        ON sid.child_hash = sid2.child_hash 
        -- Safety check: if hash collision (extremely unlikely), we verify the text
        AND sid.child_object_id_text = sid2.child_object_id_text 
        AND sid2.objectclass_id = 901 -- sid2 is the surface
    JOIN objectclass oc ON oc.id = sid.objectclass_id
    JOIN geometry_data gd ON gd.id = sid.geometry_data_id
    JOIN property pd ON pd.feature_id = gd.feature_id
WHERE sid.objectclass_id IN (709, 710, 712); -- sid is the building
  --AND pd.name = 'Flaeche';

-- Indexes on the target table
CREATE INDEX IF NOT EXISTS {table_name}_building_objectid_idx ON {output_schema}.{table_name} (building_objectid);
-- Spatial index is expensive, create it at the end
CREATE INDEX IF NOT EXISTS {table_name}_geom_idx ON {output_schema}.{table_name} USING GIST (geom);
