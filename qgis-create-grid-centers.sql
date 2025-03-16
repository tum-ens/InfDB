--- this file is only needed for testing purposes on qgis. You dont need to create
--- a separate table for centers, it is just a simple query ST_CENTROID.
CREATE TABLE IF NOT EXISTS citydb.test_grid_centers (
    id SERIAL PRIMARY KEY,
    geom GEOMETRY(POINT, 4326)
);

INSERT INTO citydb.test_grid_centers (geom)
WITH center AS (
    SELECT ST_Centroid(geom) AS grid_center
    FROM citydb.test_grid
)
SELECT DISTINCT grid_center
FROM center;
