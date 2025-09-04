-- fill floor_number column
WITH floor_number_data AS (SELECT feature_id, val_int
                           FROM property
                           WHERE name = 'storeysAboveGround')
UPDATE {output_schema}.buildings
SET floor_number = GREATEST(fnd.val_int, 1)
FROM floor_number_data fnd
WHERE id = fnd.feature_id;

-- fill in missing floor_number values
WITH average_floor_height AS (SELECT building_use_id,
                                     PERCENTILE_CONT(0.5) WITHIN GROUP ( ORDER BY (height / floor_number) ) as height_per_floor
                              FROM {output_schema}.buildings
                              GROUP BY building_use_id)
UPDATE {output_schema}.buildings b
SET floor_number = GREATEST(ROUND(height / COALESCE(afh.height_per_floor, height)), 1)
FROM average_floor_height afh
WHERE b.floor_number IS NULL
  AND b.building_use_id = afh.building_use_id;
