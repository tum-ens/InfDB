-- ============================================================
-- Fortiss-style helper tables for building view generation.
--
-- These materialize one row per feature_id for each attribute,
-- so the final view is a set of fast B-tree FK joins instead of
-- a large MAX(CASE WHEN ...) pivot.
--
-- Source tables (feature, property, geometry_data, address) live
-- in the citydb schema (resolved via search_path).
-- All helpers are created in {helper_schema}.
--
-- NOTE on SRID: unlike the original fortiss SQL we do NOT hard-cast
-- the geometry to a fixed EPSG (e.g. 25832). We keep ST_Multi(...)
-- so the column inherits the source SRID. This avoids breaking on
-- UTM33 federal states while producing identical results for UTM32.
-- ============================================================

DROP SCHEMA IF EXISTS {helper_schema} CASCADE;
CREATE SCHEMA {helper_schema};


-- 1. Gemeindeschluessel (one per feature)
CREATE TABLE {helper_schema}.helper_gemeindeschluessel AS
SELECT DISTINCT ON (feature_id)
    feature_id,
    val_string AS gemeindeschluessel
FROM property
WHERE name = 'Gemeindeschluessel'
  AND val_string IS NOT NULL
ORDER BY feature_id, id;
CREATE INDEX ON {helper_schema}.helper_gemeindeschluessel (feature_id);


-- 2. Building function
CREATE TABLE {helper_schema}.helper_function AS
SELECT DISTINCT ON (feature_id)
    feature_id,
    val_string AS building_function_code
FROM property
WHERE name = 'function'
  AND val_string IS NOT NULL
ORDER BY feature_id, id;
CREATE INDEX ON {helper_schema}.helper_function (feature_id);


-- 3. Roof type
CREATE TABLE {helper_schema}.helper_rooftype AS
SELECT DISTINCT ON (feature_id)
    feature_id,
    val_string::integer AS rooftype_code
FROM property
WHERE name = 'roofType'
  AND val_string IS NOT NULL
ORDER BY feature_id, id;
CREATE INDEX ON {helper_schema}.helper_rooftype (feature_id);


-- 4. Grundrissaktualitaet
CREATE TABLE {helper_schema}.helper_grundrissaktualitaet AS
SELECT DISTINCT ON (feature_id)
    feature_id,
    val_string AS grundrissaktualitaet
FROM property
WHERE name = 'Grundrissaktualitaet'
  AND val_string IS NOT NULL
ORDER BY feature_id, id;
CREATE INDEX ON {helper_schema}.helper_grundrissaktualitaet (feature_id);


-- 5. Storeys above ground (handles multiple naming conventions across states)
CREATE TABLE {helper_schema}.helper_storeys AS
SELECT DISTINCT ON (feature_id)
    feature_id,
    val_int AS storeysaboveground
FROM property
WHERE name = ANY (ARRAY[
    'storeysAboveGround',
    'numberOfStoreysAboveGround',
    'anzahlGeschosse',
    'geschossanzahl',
    'levelsAboveGround'
])
  AND val_int IS NOT NULL
ORDER BY feature_id, id;
CREATE INDEX ON {helper_schema}.helper_storeys (feature_id);


-- 6. Height (priority: measuredHeight > height > value)
CREATE TABLE {helper_schema}.helper_height AS
SELECT DISTINCT ON (feature_id)
    feature_id,
    val_double,
    val_int,
    val_string
FROM property
WHERE name = ANY (ARRAY['measuredHeight', 'height', 'value'])
  AND (val_double IS NOT NULL OR val_int IS NOT NULL OR val_string IS NOT NULL)
ORDER BY
    feature_id,
    CASE name
        WHEN 'measuredHeight' THEN 1
        WHEN 'height'         THEN 2
        WHEN 'value'          THEN 3
        ELSE 4
    END,
    id;
CREATE INDEX ON {helper_schema}.helper_height (feature_id);


-- 7. Address (street / house_number split, robust to both encodings)
CREATE TABLE {helper_schema}.helper_address AS
SELECT
    p.feature_id,
    array_agg(DISTINCT
        CASE
            WHEN a.house_number IS NULL THEN regexp_replace(a.street, '\s+\d[\d\w]*$', '')
            ELSE a.street
        END) AS street,
    array_agg(DISTINCT
        CASE
            WHEN a.house_number IS NULL THEN (regexp_match(a.street, '\d[\d\w]*$'))[1]
            ELSE a.house_number
        END) AS house_number,
    (array_agg(a.city ORDER BY a.id))[1]     AS city,
    (array_agg(a.state ORDER BY a.id))[1]    AS state,
    (array_agg(a.zip_code ORDER BY a.id))[1] AS zip_code
FROM property p
JOIN citydb.address a ON a.id = p.val_address_id
WHERE p.name = 'address'
  AND p.val_address_id IS NOT NULL
GROUP BY p.feature_id;
CREATE INDEX ON {helper_schema}.helper_address (feature_id);


-- 8. Building parts (parent -> part), one row per part
CREATE TABLE {helper_schema}.helper_building_parts AS
SELECT
    feature_id     AS parent_feature_id,
    val_feature_id AS part_feature_id
FROM property
WHERE name = 'buildingPart'
  AND val_feature_id IS NOT NULL;
CREATE INDEX ON {helper_schema}.helper_building_parts (parent_feature_id);
CREATE INDEX ON {helper_schema}.helper_building_parts (part_feature_id);


-- 9. lod2Solid geometry (extract polygon faces from the PolyhedralSurface)
CREATE TABLE {helper_schema}.helper_lod2solid_geom AS
SELECT DISTINCT ON (p.feature_id)
    p.feature_id,
    ST_Multi(ST_CollectionExtract(gd.geometry, 3)) AS geometry
FROM property p
JOIN geometry_data gd ON gd.id = p.val_geometry_id
WHERE p.name = 'lod2Solid'
  AND p.val_geometry_id IS NOT NULL
  AND gd.geometry IS NOT NULL
  AND NOT ST_IsEmpty(gd.geometry)
  AND NOT ST_IsEmpty(ST_CollectionExtract(gd.geometry, 3))
ORDER BY
    p.feature_id,
    COALESCE(ST_Area(ST_CollectionExtract(gd.geometry, 3)), 0) DESC,
    gd.id;
CREATE INDEX ON {helper_schema}.helper_lod2solid_geom (feature_id);
CREATE INDEX ON {helper_schema}.helper_lod2solid_geom USING GIST (geometry);


-- 10. Building objectid -> gemeindeschluessel
-- Used to attach gemeindeschluessel to building_surface AT CREATE TIME (one join
-- in the CREATE) instead of a full-table UPDATE afterwards. The UPDATE rewrites
-- every surface row (MVCC) and scales badly for whole federal states.
CREATE TABLE {helper_schema}.helper_bld_gemeindeschluessel AS
SELECT f.objectid AS building_objectid,
       h.gemeindeschluessel
FROM feature f
JOIN {helper_schema}.helper_gemeindeschluessel h ON h.feature_id = f.id
WHERE f.objectclass_id = 901;
CREATE INDEX ON {helper_schema}.helper_bld_gemeindeschluessel (building_objectid);


-- ============================================================
-- Refresh planner statistics. Without this the freshly created
-- helper tables have no stats and the final view query can pick a
-- catastrophic plan (observed: ~380s vs ~2s with stats).
-- ============================================================
ANALYZE {helper_schema}.helper_bld_gemeindeschluessel;
ANALYZE {helper_schema}.helper_gemeindeschluessel;
ANALYZE {helper_schema}.helper_function;
ANALYZE {helper_schema}.helper_rooftype;
ANALYZE {helper_schema}.helper_grundrissaktualitaet;
ANALYZE {helper_schema}.helper_storeys;
ANALYZE {helper_schema}.helper_height;
ANALYZE {helper_schema}.helper_address;
ANALYZE {helper_schema}.helper_building_parts;
ANALYZE {helper_schema}.helper_lod2solid_geom;
