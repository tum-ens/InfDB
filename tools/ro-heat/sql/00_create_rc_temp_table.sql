DROP TABLE IF EXISTS temp_rc_calculation;

CREATE TEMP TABLE temp_rc_calculation AS
WITH wall_data AS (
    SELECT
        building_objectid,
        SUM(area) AS wall_surface_area
    FROM (
        SELECT
            regexp_replace(f.objectid, '_[^_]*-.*$', '') AS building_objectid,
            CAST(p.val_string AS double precision) AS area
        FROM feature f
        JOIN geometry_data gd ON f.id = gd.feature_id
        JOIN property p ON gd.feature_id = p.feature_id
        WHERE f.objectclass_id = 709 -- WallSurface
          AND p.name = 'Flaeche'
    ) sub
    GROUP BY building_objectid
),
roof_data AS (
    SELECT
        building_objectid,
        SUM(area) AS roof_surface_area
    FROM (
        SELECT
            regexp_replace(f.objectid, '_[^_]*-.*$', '') AS building_objectid,
            CAST(p.val_string AS double precision) AS area
        FROM feature f
        JOIN geometry_data gd ON f.id = gd.feature_id
        JOIN property p ON gd.feature_id = p.feature_id
        WHERE f.objectclass_id = 712 -- RoofSurface
          AND p.name = 'Flaeche'
    ) sub
    GROUP BY building_objectid
)

SELECT
    b.id AS building_id,
    b.floor_area,
    b.floor_number,
    b.building_type,
    b.construction_year,
    -- Reduce wall surface by the assumed window area, see below
    wd.wall_surface_area - b.floor_area * b.floor_number * 0.75 * 0.2 AS wall_area,
    rd.roof_surface_area AS roof_area,
    -- Assume heated area = b.floor_area * b.floor_number * 0.75
    -- Assume window area to be 0.2 m² per heated area ()
    b.floor_area * b.floor_number * 0.75 * 0.2 AS window_area
FROM pylovo_input.buildings b
LEFT JOIN wall_data wd ON b.objectid = wd.building_objectid
LEFT JOIN roof_data rd ON b.objectid = rd.building_objectid;
SELECT * from temp_rc_calculation
WHERE building_type IS NOT NULL