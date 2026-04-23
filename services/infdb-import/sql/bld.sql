DO $$
DECLARE
    v_changelog_id BIGINT;
BEGIN

-- ANALYZE feature;
-- ANALYZE property;

-- Indexes are now created in utils.create_table_building() to avoid deadlocks in parallel processing

CREATE SCHEMA IF NOT EXISTS {output_schema};

-- Drop existing partition to avoid conflict with wrong ags_id value
-- DROP TABLE IF EXISTS {output_schema}.{table_name} CASCADE;
CREATE TABLE IF NOT EXISTS {output_schema}.{table_name}
    PARTITION OF opendata.building_lod2 
    FOR VALUES IN ('{ags_id}');

SELECT public.fn_begin_changelog('infdb-import'::TEXT, 'no comment'::TEXT, session_user::TEXT, NULL::TEXT, NULL::BIGINT) INTO v_changelog_id;

-- INSERT without re-joining property
INSERT INTO {output_schema}.{table_name} (
    ags_id, feature_id, objectid, gemeindeschluessel, objectclass_id,
    height, storeysaboveground, building_function_code, zip_code, street, 
    house_number, city, country, state,
    changelog_id  -- ← added
)
WITH base_buildings AS (
    SELECT
        f.id AS feature_id,
        f.objectclass_id,
        f.objectid,
        MAX(CASE WHEN p.name = 'function' THEN p.val_string END) AS building_function_code,
        MAX(CASE WHEN p.name = 'Gemeindeschluessel' THEN p.val_string END) AS gemeindeschluessel,
        MAX(CASE WHEN p.name = 'storeysAboveGround' THEN p.val_int END) AS storeysaboveground,
        LEFT(MAX(CASE WHEN p.name = 'Gemeindeschluessel' THEN p.val_string END), 2) AS ags_id,
        MAX(CASE WHEN p.name = 'address' THEN p.val_address_id END) AS address_id,
        MAX(CASE WHEN p.name = 'value' THEN p.val_double END) AS height  -- This assumes 'value' with parent 'height' is the correct height property since unique constraint is not guaranteed. We will filter by parent_id in the height_data CTE.
        -- MAX(CASE WHEN p.name = 'height' THEN p.val_double END) AS height_parent_id
    FROM feature f
            INNER JOIN property p ON f.id = p.feature_id
    WHERE f.objectclass_id = 901 
        AND f.objectid LIKE '{object_id_prefix}%'
        AND p.name IN ('function', 'Gemeindeschluessel', 'storeysAboveGround', 'address', 'value') -- add 'height' if height_parent_id is used
    GROUP BY f.id, f.objectclass_id, f.objectid
    HAVING MAX(CASE WHEN p.name = 'function' THEN p.val_string END) >= '31001_'
    AND MAX(CASE WHEN p.name = 'function' THEN p.val_string END) < '31002'
    -- AND MAX(CASE WHEN p.name = 'Gemeindeschluessel' THEN p.val_string END) IN ({ags})
)
SELECT
    bb.ags_id,
    bb.feature_id,
    bb.objectid,
    bb.gemeindeschluessel,
    bb.objectclass_id,
    bb.height,
    bb.storeysaboveground,
    bb.building_function_code,
    adr.zip_code,
    regexp_replace(trim(adr.street), '\s*\d+[\w,]*$', '') AS street,
    (regexp_match(trim(adr.street), '\s*(\d+[\w,]*)$'))[1] AS house_number,
    adr.city, 
    adr.country, 
    adr.state,
    v_changelog_id  -- ← all rows get the same changelog_id
FROM base_buildings bb
    LEFT JOIN citydb.address adr ON bb.address_id = adr.id;

END;
$$;