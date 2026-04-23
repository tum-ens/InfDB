------------------------------------------------------
-- Create linking table between building and (sub)surfaces
------------------------------------------------------

-- Indexes on 3D CDB to speed up the join and filtering
CREATE INDEX IF NOT EXISTS geometry_data_geometry_properties_index 
            ON citydb.geometry_data USING gin (geometry_properties);
CREATE INDEX IF NOT EXISTS idx_feature_objectclass 
            ON feature(objectclass_id);
CREATE INDEX IF NOT EXISTS idx_feature_objectid 
            ON feature(objectid);

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