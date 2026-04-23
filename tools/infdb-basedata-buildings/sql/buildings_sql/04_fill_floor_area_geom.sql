-- Summary: Updates the geom, centroid, and floor_area columns and
-- removes small buildings with a floor area of less than 12 square meters.

-- Part 1: fill floor_area from temp_building_surface
WITH ground_data AS (
    SELECT
        sur.building_objectid,
        sur.area
    FROM temp_building_surface sur
    WHERE sur.objectclass_id = 710 -- 710 = ground surface
)
UPDATE temp_buildings b
SET floor_area = gd.area
FROM ground_data gd
WHERE b.objectid = gd.building_objectid;

-- Part 2: fill geom and centroid from building_view
WITH geom_data AS (
    SELECT
        feature_id,
        ST_Transform(ST_Force2D(b.geom), {EPSG}) AS geom
    FROM {input_schema}.building_view b
    WHERE b.gemeindeschluessel = '{ags}'
)
UPDATE temp_buildings b
SET geom     = gd.geom,
    centroid = ST_Centroid(gd.geom)
FROM geom_data gd
WHERE b.feature_id = gd.feature_id;

-- delete buildings below an area threshold
DELETE
FROM temp_buildings b
WHERE b.floor_area < 12;