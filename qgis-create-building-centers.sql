--- This file is for testing purposeses, building locations are not necessary for us
---  to save for because we want to map buildings with the grid itself.
CREATE TABLE IF NOT EXISTS citydb.test_building_points (
    building_id INTEGER PRIMARY KEY,
    geom GEOMETRY(Point, 4326)
);

INSERT INTO citydb.test_building_points (building_id, geom)
SELECT b.id AS building_id,
       ST_SetSRID(ST_Centroid(c.envelope), 4326) AS geom
FROM citydb.building b
JOIN citydb.cityobject c ON b.id = c.id;


