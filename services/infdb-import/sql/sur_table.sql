-- Analysis helps the query planner understand statistics for the join
--ANALYZE tmp_bld.{table_name}_ids;

-- Start from scratch: Drop existing table to avoid conflicts
DROP TABLE IF EXISTS {output_schema}.{table_name} CASCADE;

-- EXPLAIN ANALYZE
CREATE TABLE {output_schema}.{table_name} AS
SELECT
    sid2.building_objectid,
    sid.objectclass_id,
    oc.classname,
    MAX(CASE WHEN p_ged.name = 'Flaeche' THEN p_ged.val_string END)::double precision AS area, -- works only for bavaria
    MAX(CASE WHEN p_bld.name = 'Gemeindeschluessel' THEN p_bld.val_string END) AS gemeindeschluessel,
    ST_Multi(gd.geometry) AS geom
FROM tmp_bld.{table_name}_ids sid
    JOIN tmp_bld.{table_name}_ids sid2 
        ON sid.child_hash = sid2.child_hash -- Safety check: if hash collision (extremely unlikely), we verify the text
        AND sid.child_object_id_text = sid2.child_object_id_text 
        AND sid2.objectclass_id = 901 -- sid2 is the surface
    JOIN objectclass oc ON oc.id = sid.objectclass_id
    JOIN geometry_data gd ON gd.id = sid.geometry_data_id
    JOIN property p_ged ON p_ged.feature_id = gd.feature_id
    JOIN feature f ON f.objectid = sid2.building_objectid AND f.objectclass_id = 901
    JOIN property p_bld ON p_bld.feature_id = f.id AND p_bld.name = 'Gemeindeschluessel'
WHERE sid.objectclass_id IN (709, 710, 712) -- sid is the building
GROUP BY sid2.building_objectid, sid.objectclass_id, oc.classname, gd.geometry;

-- Indexes on the target table
CREATE INDEX IF NOT EXISTS {table_name}_building_objectid_idx ON {output_schema}.{table_name} (building_objectid);
CREATE INDEX IF NOT EXISTS {table_name}_geom_idx ON {output_schema}.{table_name} USING GIST (geom);