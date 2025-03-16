CREATE TABLE IF NOT EXISTS citydb.test_building_grid_map (
    building_id INTEGER NOT NULL references "building",
    grid_id INTEGER NOT NULL references "test_grid"
);

with building_locations AS (
	SELECT b.id AS building_id,
	       ST_SetSRID(ST_Centroid(c.envelope), 4326) AS geom
	FROM citydb.building b
	JOIN citydb.cityobject c ON b.id = c.id
)

INSERT INTO citydb.test_building_grid_map (building_id, grid_id)
SELECT p.building_id,
       (
         SELECT g.id
         FROM citydb.test_grid g
         WHERE ST_Within(p.geom, g.geom)
         LIMIT 1
       ) AS grid_id
FROM building_locations p;