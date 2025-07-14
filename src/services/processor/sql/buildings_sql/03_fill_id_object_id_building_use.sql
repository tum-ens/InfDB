-- Fill id, objectid and building use columns
INSERT INTO pylovo_input.buildings (id, objectid, building_use, building_use_id)
SELECT f.id,
       f.objectid,
       pylovo_input.classify_building_use(p.val_string) as building_use,
       p.val_string                                     as building_use_id
FROM feature f
         JOIN property p ON f.id = p.feature_id
WHERE f.objectclass_id = 901
  AND p.namespace_id = 10
  AND p.name = 'function'
  AND p.val_string LIKE '31001_%'  -- only allow buildings
  AND p.val_string <> '31001_2463' -- exclude garages
  AND p.val_string <> '31001_2513' -- exclude water containers
ORDER BY f.id;
