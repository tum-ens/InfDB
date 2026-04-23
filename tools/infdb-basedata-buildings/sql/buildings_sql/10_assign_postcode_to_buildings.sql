-- Summary: Assigns postal codes to buildings. It performs a spatial join
-- between building centroids and a temporary table containing postal code
-- geometries.

DROP TABLE IF EXISTS temp_postcode_{EPSG};
CREATE TEMP TABLE IF NOT EXISTS temp_postcode_{EPSG}
(
    plz int,
    geom geometry(Multipolygon, {EPSG})
);

CREATE INDEX IF NOT EXISTS idx_temp_postcode_geom ON temp_postcode_{EPSG} USING GIST (geom);

INSERT INTO temp_postcode_{EPSG} (plz, geom)
SELECT plz::int, ST_Transform(geom, {EPSG})
FROM {input_schema}."postcodes_germany";

UPDATE temp_buildings b
SET postcode = plz::int
FROM temp_postcode_{EPSG} p
WHERE p.geom && b.geom -- prefilter with bounding box &&
  AND ST_Contains(p.geom, b.centroid);
