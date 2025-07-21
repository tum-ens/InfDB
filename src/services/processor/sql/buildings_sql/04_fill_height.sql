-- fill height column
WITH height_data AS (SELECT p.feature_id, p.val_double
                     FROM property p
                     WHERE p.name = 'value'
                       AND p.parent_id IN (SELECT id FROM property WHERE name = 'height'))
UPDATE pylovo_input.buildings
SET height = hd.val_double
FROM height_data hd
WHERE id = hd.feature_id;

-- delete buildings below a height threshold
DELETE
FROM pylovo_input.buildings
WHERE height < 3.5;