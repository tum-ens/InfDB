-- fill geom and floor_area columns
WITH ground_data AS (
    SELECT regexp_replace(f.objectid, '_[^_]*-.*$', '') as building_objectid,
        cast(p.val_string as double precision)          as area,
        ST_Transform(ST_Force2D(gd.geometry), 3035)     as geometry
    FROM feature f
          JOIN geometry_data gd ON f.id = gd.feature_id
          JOIN property p ON gd.feature_id = p.feature_id
    WHERE f.objectclass_id = 710 -- GroundSurface
    AND p.name = 'Flaeche'
)
UPDATE pylovo_input.buildings
SET floor_area = gd.area,
    geom       = gd.geometry,
    centroid   = ST_Centroid(gd.geometry)
FROM ground_data gd
WHERE objectid = building_objectid;

-- delete buildings below an area threshold
DELETE
FROM pylovo_input.buildings
WHERE buildings.floor_area < 12;