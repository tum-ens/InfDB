-- Drop and recreate temp table with postcodes
DROP TABLE IF EXISTS temp_postcode_3035_ways;

CREATE TEMP TABLE IF NOT EXISTS temp_postcode_3035_ways
(
    plz int,
    geometry geometry(Multipolygon, 3035)
);

-- Insert transformed geometries
INSERT INTO temp_postcode_3035_ways (plz, geometry)
SELECT plz::int, geom FROM {output_schema}.postcode;

CREATE INDEX ON temp_postcode_3035_ways USING GIST (geometry);

-- Update ways with postcode based on intersection with postcode multipolygons
UPDATE {output_schema}.ways w
SET postcode = p.plz
FROM temp_postcode_3035_ways p
WHERE ST_Intersects(ST_Centroid(w.geom), p.geometry);

