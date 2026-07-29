-- Summary: Updates the geom, centroid, and floor_area columns and
-- removes small buildings with a floor area of less than 12 square meters.

-- Build per-building 2D footprint + centroid from the ground surfaces (710)
-- of the fortiss building_surface. This replaces the footprint/centroid that
-- the old building_view exposed (the fortiss building_view geometry is the 3D
-- lod2Solid, not a footprint). Geometry stays in the source SRID (e.g. 25832),
-- so it is a drop-in for the former building_view.geom / building_view.centroid
-- in this file and in 06_prepare_grid / 11_create_building_to_grid.
--
-- A building's ground faces are unioned into a single footprint. Each face is
-- normalized with ST_MakeValid so the union is well defined for any source
-- polygon, and ST_CollectionExtract(..., 3) keeps the polygonal parts of the
-- union, yielding a MultiPolygon for the geom/centroid target columns.
DROP TABLE IF EXISTS temp_building_footprint;
CREATE TEMP TABLE temp_building_footprint AS
WITH footprint AS (
    SELECT
        bs.building_objectid,
        ST_CollectionExtract(
            ST_Union(ST_MakeValid(ST_Force2D(bs.geometry))), 3
        ) AS geom
    FROM {input_schema}.building_surface bs
    WHERE bs.objectclass_id = 710 -- 710 = ground surface
      AND bs.gemeindeschluessel = '{ags}'
    GROUP BY bs.building_objectid
)
SELECT
    building_objectid,
    geom,
    ST_PointOnSurface(geom) AS centroid
FROM footprint;

CREATE INDEX ON temp_building_footprint USING GIST (geom);
CREATE INDEX ON temp_building_footprint (building_objectid);

-- Part 1: fill floor_area from temp_building_surface.
-- SUM over the ground surfaces per building so multi-part buildings (and any
-- building with several 710 faces) get the total footprint area, not one face.
WITH ground_data AS (
    SELECT
        sur.building_objectid,
        SUM(sur.area) AS area
    FROM temp_building_surface sur
    WHERE sur.objectclass_id = 710 -- 710 = ground surface
    GROUP BY sur.building_objectid
)
UPDATE temp_buildings b
SET floor_area = gd.area
FROM ground_data gd
WHERE b.objectid = gd.building_objectid;

-- Part 2: fill geom and centroid from the ground-surface footprint
WITH geom_data AS (
    SELECT
        building_objectid,
        ST_Transform(geom, {EPSG}) AS geom
    FROM temp_building_footprint
)
UPDATE temp_buildings b
SET geom     = gd.geom,
    centroid = ST_Centroid(gd.geom)
FROM geom_data gd
WHERE b.objectid = gd.building_objectid;

-- delete buildings below an area threshold
DELETE
FROM temp_buildings b
WHERE b.floor_area < 12;
