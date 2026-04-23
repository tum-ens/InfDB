-- ============================================================
-- Assign `address_street_id` for buildings by matching their parsed address street
-- to nearby named road centerlines (ways) within a given municipality (AGS).
--
-- Goal:
-- - For each building in `{output_schema}.buildings` for a specific `{ags}`,
--   find the closest matching way (by street name) and write its id into
--   `address_street_id`.
--
-- Approach (high level):
-- 1) Build a temp table of candidate ways (names + geometry) restricted to the AGS area.
-- 2) Build a temp table of building street names parsed from CityDB addresses (restricted to AGS).
-- 3) Update buildings by joining on street-name equality and choosing the closest way as a tie-breaker.
--
-- Notes:
-- - Street matching uses exact equality against both `name` and `name_kurz`.
-- - `DISTINCT ON (building_id)` + `ORDER BY ... <-> ...` ensures only the nearest match is picked
--   when multiple ways share the same street name.
-- - Temporary tables are indexed to keep matching and spatial filtering fast.
-- ============================================================


-- ============================================================
-- Step 1: Collect candidate way names (roads) within the AGS boundary
--
-- Purpose:
-- - Restrict the road/way dataset to the municipality defined by `{ags}` to reduce
--   join cardinality and improve performance.
--
-- Input:
-- - `{input_schema}.basemap_verkehrslinie` (ways / road centerlines)
-- - `{input_schema}.bkg_vg5000_gem` (municipality polygons, provides `ags` + `geom`)
--
-- Output:
-- - `temp_way_names` contains:
--   - `way_id`: unique id (cast to bigint to match `buildings.address_street_id`)
--   - `geom`: way geometry
--   - `name`, `name_kurz`: long/short street names used for matching
-- ============================================================
CREATE TEMP TABLE temp_way_names AS
SELECT
    v.ogc_fid::bigint AS way_id,  -- cast to bigint to match address_street_id column type
    v.geom,
    v.name,
    v.name_kurz
FROM {input_schema}.basemap_verkehrslinie v
JOIN {input_schema}.bkg_vg5000_gem g
    ON g.ags = '{ags}'                      -- restrict to the target municipality
    AND ST_Intersects(v.geom, g.geom);      -- keep only ways intersecting the municipality polygon

-- Performance indexes:
-- - B-tree indexes for fast equality matching on names and ID
-- - GiST index for spatial predicates / nearest-neighbor ordering
CREATE INDEX ON temp_way_names(name);
CREATE INDEX ON temp_way_names(name_kurz);
CREATE INDEX ON temp_way_names(way_id);
CREATE INDEX ON temp_way_names USING GIST (geom);


-- ============================================================
-- Step 2: Extract / normalize building street names from CityDB addresses
--
-- Purpose:
-- - Produce a per-building street-name field used to match to way names.
-- - CityDB may store multiple street entries separated by ';' (e.g., multiple address lines),
--   so we split them and normalize each entry.
--
-- Parsing logic:
-- - `unnest(string_to_array(a.street, ';'))` splits multiple street strings
-- - `trim(...)` removes leading/trailing whitespace
-- - `regexp_replace(..., '\s*\d+[\w,]*$', '')` removes trailing house-number-like suffixes
--   (e.g., "Main Street 12a" -> "Main Street")
--
-- Scope restriction:
-- - Only buildings where `gemeindeschluessel = '{ags}'`
--
-- Output:
-- - `temp_building_addresses` contains:
--   - `building_id`: building PK from `{output_schema}.buildings`
--   - `geom`: building geometry (used for distance / nearest-way selection)
--   - `street`: parsed street string used for matching
-- ============================================================
CREATE TEMP TABLE temp_building_addresses AS
SELECT
    b.id AS building_id,
    b.geom,
    b.centroid,                                                               -- add centroid for distance calculations
    regexp_replace(trim(individual_street), '\s*\d+[\w,]*$', '') AS street
FROM {output_schema}.buildings b
JOIN citydb.property p ON b.feature_id = p.feature_id
JOIN citydb.address a ON p.val_address_id = a.id
CROSS JOIN LATERAL unnest(string_to_array(a.street, ';')) AS individual_street
WHERE b.gemeindeschluessel = '{ags}';

CREATE INDEX ON temp_building_addresses(street);
CREATE INDEX ON temp_building_addresses USING GIST (geom);
CREATE INDEX ON temp_building_addresses USING GIST (centroid);              -- index centroid for spatial ops


-- ============================================================
-- Step 3: Update buildings.address_street_id using nearest matching way
--
-- Matching conditions:
-- - Street name must match either:
--   - `temp_way_names.name` OR
--   - `temp_way_names.name_kurz`
--
-- Spatial constraint:
-- - Only consider candidate ways within a fixed radius of the building:
--   `ST_DWithin(ba.geom, wn.geom, 1000)`
--
-- Tie-breaking:
-- - If multiple ways match the street name for a building, pick the closest one:
--   `ORDER BY ba.building_id, wn.geom <-> ba.geom`
--   and keep only the first row per building via `DISTINCT ON (ba.building_id)`.
--
-- Update safety:
-- - Only update rows for this `{ags}`.
-- - `IS DISTINCT FROM` avoids unnecessary writes and correctly handles NULL comparisons.
-- ============================================================
UPDATE {output_schema}.buildings AS b
SET address_street_id = w.way_id
FROM (
    SELECT DISTINCT ON (ba.building_id)
        ba.building_id,
        wn.way_id
    FROM temp_building_addresses AS ba
    JOIN temp_way_names wn
        ON ba.street = wn.name
        OR ba.street = wn.name_kurz
    WHERE ST_DWithin(ba.centroid, wn.geom, 1000)          -- distance from building centroid to way
    ORDER BY ba.building_id, wn.geom <-> ba.centroid       -- nearest way to centroid as tiebreaker
) w
WHERE b.id = w.building_id
  AND b.gemeindeschluessel = '{ags}'
  AND b.address_street_id IS DISTINCT FROM w.way_id;


-- ============================================================
-- Cleanup: drop temporary tables (session-local)
-- ============================================================
DROP TABLE temp_way_names;
DROP TABLE temp_building_addresses;