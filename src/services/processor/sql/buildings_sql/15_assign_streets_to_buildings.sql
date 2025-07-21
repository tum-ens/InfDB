CREATE INDEX IF NOT EXISTS idx_way_names_name ON pylovo_input.way_names(name);
CREATE INDEX IF NOT EXISTS idx_way_names_name_kurz ON pylovo_input.way_names(name_kurz);
CREATE INDEX IF NOT EXISTS idx_way_names_way_id ON pylovo_input.way_names(way_id);

CREATE INDEX IF NOT EXISTS idx_ways_geom ON pylovo_input.ways USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_building_addresses_id ON pylovo_input.building_addresses(building_id);

-- Step 1: Create a temporary table holding the closest way ID for each building
DROP TABLE IF EXISTS temp_closest_ways;
CREATE TEMP TABLE temp_closest_ways AS
SELECT
    ba.building_id,
    w.way_id AS way_id_by_address
FROM pylovo_input.building_addresses AS ba
JOIN pylovo_input.buildings AS b ON ba.building_id = b.id
JOIN pylovo_input.way_names wn ON ba.street = wn.name OR ba.street = wn.name_kurz
JOIN LATERAL (
    SELECT w.way_id, w.geom
    FROM pylovo_input.ways AS w
    WHERE w.way_id = wn.way_id
    ORDER BY w.geom <-> b.geom
    LIMIT 1
) w ON true;

-- Step 2: Update buildings_combined with closest way ID
UPDATE pylovo_input.buildings AS b
SET address_street_id = t.way_id_by_address
FROM temp_closest_ways AS t
WHERE b.id = t.building_id;
