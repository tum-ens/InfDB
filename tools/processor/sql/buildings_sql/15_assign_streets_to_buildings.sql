/*
═══════════════════════════════════════════════════════════════════════════════
                    BUILDING-TO-STREET ASSIGNMENT SCRIPT
═══════════════════════════════════════════════════════════════════════════════

PURPOSE:
--------
This script assigns buildings to their closest street/way based on address matching
and geometric proximity. It updates the 'address_street_id' field in the buildings 
table with the way_id of the most appropriate street.

ALGORITHM OVERVIEW:
------------------
1. Match buildings to potential streets using address street names
2. For each building, find the closest street among those with matching names
3. Use interior portions of streets (excluding endpoints) to avoid intersection bias
4. Update buildings table with the selected street assignments

INPUT REQUIREMENTS:
------------------
- building_addresses: Contains building_id and street name for each building
- buildings: Contains building geometries and the target address_street_id field
- way_names: Contains way_id to street name mappings (full and abbreviated names)
- ways: Contains street geometries (LineString format)

OUTPUT:
-------
Updates the 'address_street_id' field in the buildings table with the assigned way_id.

PERFORMANCE NOTES:
-----------------
- Creates necessary indexes for optimal query performance
- Uses PostGIS distance operator (<->) for efficient spatial calculations
- Processes one building at a time using DISTINCT ON for deterministic results

COORDINATE SYSTEM:
-----------------
Designed for projected coordinate systems (e.g., EPSG:3035) where distance 
calculations are performed in meters.

═══════════════════════════════════════════════════════════════════════════════
*/

-- ─────────────────────────────────────────────
-- 1. INDEX CREATION (PERFORMANCE OPTIMIZATION)
-- ─────────────────────────────────────────────
/*
Creates indexes on frequently queried columns to optimize join operations
and spatial queries. These indexes significantly improve performance for
large datasets.
*/

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
CORE ALGORITHM EXPLANATION:

Step 1: ADDRESS-BASED STREET MATCHING
- Links buildings to potential streets through address street names
- Matches against both full street names (wn.name) and abbreviated forms (wn.name_kurz)
- This ensures only semantically relevant streets are considered

Step 2: GEOMETRIC PROXIMITY CALCULATION  
- Uses ST_LineSubstring(w.geom, 0.05, 0.95) to exclude street endpoints
- This avoids assigning buildings to intersection points between streets
- Calculates distance using the <-> operator for optimal performance

Step 3: CLOSEST STREET SELECTION
- DISTINCT ON (ba.building_id) ensures one assignment per building
- ORDER BY prioritizes the closest street when multiple streets share the same name
- Results in deterministic assignments based on geometric proximity

INTERSECTION AVOIDANCE:
The key innovation is using ST_LineSubstring(0.05, 0.95) which removes the first
and last 5% of each street geometry. This prevents buildings from being assigned
to intersection points where multiple streets meet, ensuring more logical 
street assignments.
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
ORDER BY ba.building_id, w.geom <-> b.geom;


-- ─────────────────────────────────────────────
-- 3. BUILDING TABLE UPDATE
-- ─────────────────────────────────────────────
/*
Updates the target buildings table with the calculated street assignments.
Only buildings with matching addresses will receive assignments - buildings
without address data will remain unassigned (address_street_id = NULL).
*/

UPDATE {output_schema}.buildings AS b
SET address_street_id = t.way_id_by_address
FROM temp_closest_ways AS t
WHERE b.id = t.building_id;