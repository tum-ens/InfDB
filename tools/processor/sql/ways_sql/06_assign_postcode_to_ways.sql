/*
═══════════════════════════════════════════════════════════════════════════════
              ASSIGNING POSTCODES TO ROAD SEGMENTS (WAYS)
═══════════════════════════════════════════════════════════════════════════════

PURPOSE:
--------
This script assigns postal codes (PLZ) to street segments (ways) based on
spatial intersection between the centroid of each road geometry and the
polygon geometry of postcode regions.


ALGORITHM OVERVIEW:
-------------------
1. Create a temporary table with postcode geometries in EPSG:3035
2. Use centroids of ways to avoid overmatching in dense intersection areas
3. Perform spatial join with `ST_Intersects` to assign PLZs
4. Index the postcode polygons for faster intersection queries

INPUT REQUIREMENTS:
-------------------
- {output_schema}.postcode: Contains `plz` and `geom` columns (geometry in SRID 3035)
- {output_schema}.ways: Contains road segment geometries to be updated

OUTPUT:
-------
- Updates the `postcode` column in {output_schema}.ways with the matching `plz`

═══════════════════════════════════════════════════════════════════════════════
*/

-- ─────────────────────────────────────────────
-- 1. TEMP TABLE: TRANSFORMED POSTCODE GEOMETRIES
-- ─────────────────────────────────────────────

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


-- ─────────────────────────────────────────────
-- 2. POSTCODE ASSIGNMENT TO WAYS
-- ─────────────────────────────────────────────

UPDATE {output_schema}.ways w
SET postcode = p.plz
FROM temp_postcode_3035_ways p
WHERE ST_Intersects(ST_Centroid(w.geom), p.geometry);

