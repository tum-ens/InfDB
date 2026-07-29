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
-- DISTINCT ON (objectid): fortiss building_view has one row per building part
-- (902), so a multi-part building appears multiple times with the same objectid.
-- buildings.objectid is UNIQUE, so we collapse to one row per building and pick
-- the tallest part as the representative (its feature_id drives height/storeys
-- joins in 03/05).
SELECT DISTINCT ON (b.objectid)
       b.feature_id,
       b.objectid,
       {output_schema}.classify_building_use(b.building_function_code) as building_use,
       b.building_function_code                                     as building_use_id,
       array_to_string(b.street, ', ')        as street,        -- fortiss building_view: street is text[]
       array_to_string(b.house_number, ', ')  as house_number,  -- fortiss building_view: house_number is text[]
       b.gemeindeschluessel
FROM {input_schema}.building_view b
WHERE b.gemeindeschluessel = '{ags}'
  AND building_function_code LIKE '31001_%'  -- only allow buildings
  AND building_function_code <> '31001_2463' -- exclude garages
  AND building_function_code <> '31001_2513' -- exclude water containers
  AND b.geometry IS NOT NULL
ORDER BY b.objectid, b.height DESC NULLS LAST;
