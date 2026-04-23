WITH wall_data AS (
        SELECT building_objectid,
               SUM(area) AS wall_surface_area
        FROM basedata.building_surface_area
        WHERE 
                classname = 'WallSurface'
                AND gemeindeschluessel LIKE '{ags}'
        GROUP BY building_objectid),
     
     roof_data AS (
        SELECT building_objectid,
               SUM(area) AS roof_surface_area
        FROM basedata.building_surface_area
        WHERE 
                classname = 'RoofSurface'
                AND gemeindeschluessel LIKE '{ags}'
        GROUP BY building_objectid)

SELECT b.objectid                                                        AS building_objectid,
       b.floor_area,
       b.floor_number,
       b.building_type,
       b.construction_year,
       -- Reduce wall surface by the assumed window area, see below
       wd.wall_surface_area - b.floor_area * b.floor_number * 0.75 * 0.2 AS wall_area,
       rd.roof_surface_area                                              AS roof_area,
       -- Assume heated area = b.floor_area * b.floor_number * 0.75
       -- Assume window area to be 0.2 m² per heated area
       b.floor_area * b.floor_number * 0.75 * 0.2                        AS window_area
FROM {input_schema}.buildings b
        LEFT JOIN wall_data wd ON b.objectid = wd.building_objectid
        LEFT JOIN roof_data rd ON b.objectid = rd.building_objectid
WHERE b.building_type IS NOT NULL 
  AND b.gemeindeschluessel LIKE '{ags}'
ORDER BY b.objectid;