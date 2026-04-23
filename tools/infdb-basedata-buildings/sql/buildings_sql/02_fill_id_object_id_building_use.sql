-- Summary: Syncs the buildings table with buildings_lod2 source data.
-- It inserts new buildings, updates existing ones, and removes obsolete entries.
-- Key attributes like objectid, building_use, and address information are
-- populated while resetting derived columns.

INSERT INTO temp_buildings (
    feature_id,
    objectid,
    building_use,
    building_use_id,
    street,
    house_number,
    gemeindeschluessel
)
SELECT
       b.feature_id,
       b.objectid,
       {output_schema}.classify_building_use(b.building_function_code) as building_use,
       b.building_function_code                                     as building_use_id,
       b.street,
       b.house_number,
       b.gemeindeschluessel
FROM {input_schema}.building_view b
WHERE b.gemeindeschluessel = '{ags}'
  AND building_function_code LIKE '31001_%'  -- only allow buildings
  AND building_function_code <> '31001_2463' -- exclude garages
  AND building_function_code <> '31001_2513' -- exclude water containers
  AND b.geom IS NOT NULL;
