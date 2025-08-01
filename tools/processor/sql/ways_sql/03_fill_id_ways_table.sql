-- Insert data into pylovo_input.ways from opendata.bmp_verkehrslinie
-- filter out classes that are not relevant for routing
-- and transform geometry to EPSG:3035 (ETRS89 / LAEA Europe)
-- calculate cost as length in km divided by speed in km/h
INSERT INTO pylovo_input.ways (
    verkehrslinie_id_basemap,
    clazz,
    geom,
    cost
)
SELECT
    v.id AS verkehrslinie_id_basemap,
    c.clazz,
    ST_Transform(v.geometry, 3035) AS geom, 
    ST_Length(ST_Transform(v.geometry, 3035)) / 1000.0 / NULLIF(c.kmh, 0) AS cost
FROM opendata.bmp_verkehrslinie v,
     LATERAL pylovo_input.map_strasse_klasse_to_class_kmh(v.klasse) AS c
WHERE v.geometry IS NOT NULL AND c.clazz NOT IN (99);

-- Set reverse_cost based on the direction of the traffic line
UPDATE pylovo_input.ways AS w
SET reverse_cost = 
  CASE 
    WHEN v.richtung = '1' THEN 1000000.0  -- one-way
    WHEN v.richtung = '0' OR v.richtung IS NULL THEN w.cost  -- bidirectional
  END
FROM opendata.bmp_verkehrslinie AS v
WHERE w.verkehrslinie_id_basemap = v.id;
