/*
═══════════════════════════════════════════════════════════════════════════════
                    BUILDING-TO-STREET ASSIGNMENT SCRIPT
═══════════════════════════════════════════════════════════════════════════════

PURPOSE:
--------
This script assigns each building to the most appropriate street segment (way),
based on address name matching and geometric proximity. The result is stored in 
the 'address_street_id' field of the buildings table.

ALGORITHM OVERVIEW:
-------------------
1. Match buildings to relevant street candidates using address street names
2. Calculate the shortest distance between the building center and the candidate
   streets' interior geometries
3. Select the closest candidate and assign its way_id to the building


INPUT REQUIREMENTS:
-------------------
- building_addresses: links buildings to street names
- buildings: includes building geometry and address_street_id field
- way_names: maps way_ids to full and short street names
- ways: contains LineString geometries of all street segments

OUTPUT:
-------
Updates the 'address_street_id' field in the buildings table with the assigned
closest way_id based on semantic and geometric criteria.

PERFORMANCE NOTES:
------------------
- Uses GIST indexes and `<->` operator for efficient spatial queries
- DISTINCT ON ensures deterministic one-to-one assignments

COORDINATE SYSTEM:
------------------
Designed for projected coordinate systems (e.g., EPSG:3035) to ensure
meter-based distance accuracy.

═══════════════════════════════════════════════════════════════════════════════
*/

-- ─────────────────────────────────────────────
-- 1. INDEX CREATION (PERFORMANCE OPTIMIZATION)
-- ─────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_way_names_name 
  ON {output_schema}.way_names(name);

CREATE INDEX IF NOT EXISTS idx_way_names_name_kurz 
  ON {output_schema}.way_names(name_kurz);

CREATE INDEX IF NOT EXISTS idx_way_names_way_id 
  ON {output_schema}.way_names(way_id);

CREATE INDEX IF NOT EXISTS idx_ways_geom 
  ON {output_schema}.ways USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_building_addresses_id 
  ON {output_schema}.building_addresses(building_id);

CREATE INDEX IF NOT EXISTS idx_building_addresses_street 
  ON {output_schema}.building_addresses(street);

CREATE INDEX IF NOT EXISTS idx_buildings_geom 
  ON {output_schema}.buildings USING GIST (geom);


-- ─────────────────────────────────────────────
-- 2. STREET ASSIGNMENT LOGIC
-- ─────────────────────────────────────────────
/*
Step 1: ADDRESS-BASED CANDIDATE SELECTION
- Matches each building’s address (ba.street) to corresponding way_ids
  via both full and abbreviated names in the way_names table.

Step 2: GEOMETRIC PROXIMITY EVALUATION
- Uses the centroid of each building geometry (`b.centroid`)
- Compares it to the geometry of the candidate street segment (`w.geom`)
- The `<->` operator efficiently calculates the distance

Step 3: CLOSEST STREET SELECTION
- DISTINCT ON ensures only the nearest segment is selected per building
*/

DROP TABLE IF EXISTS temp_closest_ways;
CREATE TEMP TABLE temp_closest_ways AS
SELECT DISTINCT ON (ba.building_id)
    ba.building_id,
    w.way_id AS way_id_by_address
FROM {output_schema}.building_addresses AS ba
JOIN {output_schema}.buildings AS b 
  ON ba.building_id = b.id
JOIN {output_schema}.way_names AS wn 
  ON ba.street = wn.name OR ba.street = wn.name_kurz
JOIN {output_schema}.ways AS w 
  ON wn.way_id = w.way_id
ORDER BY ba.building_id, b.centroid <-> w.geom;


-- ─────────────────────────────────────────────
-- 3. BUILDING TABLE UPDATE
-- ─────────────────────────────────────────────
/*
Final step: updates the buildings table with the selected way_id
Only buildings with at least one valid address-street match will be updated.
All others will retain NULL in address_street_id.
*/

UPDATE {output_schema}.buildings AS b
SET address_street_id = t.way_id_by_address
FROM temp_closest_ways AS t
WHERE b.id = t.building_id;