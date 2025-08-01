DROP TABLE IF EXISTS temp_postcode_3035;
CREATE TEMP TABLE IF NOT EXISTS temp_postcode_3035
(
    plz int,
    geometry geometry(Multipolygon, 3035)
);
INSERT INTO temp_postcode_3035 (plz, geometry)
SELECT plz::int, ST_Transform(geometry, 3035)
FROM opendata."plz_plz-5stellig";

UPDATE pylovo_input.buildings b
SET postcode = plz::int
FROM temp_postcode_3035 p
WHERE ST_Contains(geometry, b.centroid);