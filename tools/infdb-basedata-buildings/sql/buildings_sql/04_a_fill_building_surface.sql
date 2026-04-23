-- Insert raw data rows where area is not null
INSERT INTO temp_building_surface
SELECT
    bs.building_objectid,
    bs.objectclass_id,
    bs.classname,
    bs.area,
    bs.gemeindeschluessel,
    false AS is_synthetic
FROM {input_schema}.building_surface bs
WHERE bs.gemeindeschluessel = '{ags}'
  AND bs.area IS NOT NULL;

-- Insert synthetic rows where area is null, using fallback function
INSERT INTO temp_building_surface
SELECT
    bs.building_objectid,
    bs.objectclass_id,
    bs.classname,
    {output_schema}.safe_area_fallback(bs.geom) AS area,
    bs.gemeindeschluessel,
    true AS is_synthetic
FROM {input_schema}.building_surface bs
WHERE bs.gemeindeschluessel = '{ags}'
  AND bs.area IS NULL;