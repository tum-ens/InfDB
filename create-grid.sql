CREATE TABLE IF NOT EXISTS citydb.test_grid (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(POLYGON, 4326),
	CONSTRAINT geom_unique UNIQUE (geom)
);

INSERT INTO citydb.raster (geom, resolution)
WITH grid AS (
    SELECT ((ST_SquareGrid(1000, ST_Transform(envelope, 4326)))).geom 
    FROM citydb.cityobject

)
SELECT DISTINCT(geom), 1000 FROM grid;


