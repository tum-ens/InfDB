DROP TABLE IF EXISTS building_geom;

CREATE TABLE building_geom AS
SELECT DISTINCT
       f.id AS feature_id,
       g.geometry
FROM feature AS f
JOIN property AS p ON p.feature_id = f.id
JOIN geometry_data AS g ON g.id = p.feature_id;

ALTER TABLE building_geom
  ADD CONSTRAINT building_geom_pk PRIMARY KEY (feature_id);