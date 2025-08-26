/*
═══════════════════════════════════════════════════════════════════════════════
                    BUILDING-TO-STREET ASSIGNMENT SCRIPT
═══════════════════════════════════════════════════════════════════════════════

PURPOSE
-------
Assign each building to the most appropriate street segment (way) by combining
(1) semantic matching of address street names with the recorded building address and
(2) geometric proximity to pick the nearest matching segment. The selected
way_id is stored in buildings.address_street_id.

WHAT THIS SCRIPT DOES (END-TO-END)
----------------------------------
1) Builds a virtual address table by splitting multi-
   street strings into one row per street,
   parsing street and number parts.
2) Uses that virtual table to find candidate street segments by joining directly
   to WAYS using its name and name_kurz columns.
3) Among candidates, chooses the closest segment to each building centroid
   using the KNN `<->` distance operator.
4) Updates buildings.address_street_id with the chosen way_id.


INPUTS (READ)
-------------
- {output_schema}.buildings (must contain: id, centroid geometry column)
- property (links to address)
- address (contains address text, e.g., "street")
- {output_schema}.ways (LineString geometry per way_id, plus name, name_kurz)

OUTPUT (WRITE)
--------------
- Updates {output_schema}.buildings.address_street_id


COORDINATE SYSTEM
-----------------
Use a projected CRS (e.g., EPSG:3035) so `<->` reflects meter-like distances.

═══════════════════════════════════════════════════════════════════════════════
*/

-- ─────────────────────────────────────────────
-- 1) INDEX CREATION (PERFORMANCE OPTIMIZATION)
-- ─────────────────────────────────────────────

-- Speed up name lookups on ways
CREATE INDEX IF NOT EXISTS idx_ways_name 
  ON {output_schema}.ways(name);

CREATE INDEX IF NOT EXISTS idx_ways_name_kurz 
  ON {output_schema}.ways(name_kurz);

-- KNN needs GiST/SP-GiST on the right-hand geom
CREATE INDEX IF NOT EXISTS idx_ways_geom 
  ON {output_schema}.ways USING GIST (geom);

-- If centroid is frequently used in proximity searches
CREATE INDEX IF NOT EXISTS idx_buildings_centroid 
  ON {output_schema}.buildings USING GIST (centroid);

-- ─────────────────────────────────────────────
-- 2) STREET ASSIGNMENT LOGIC
-- ─────────────────────────────────────────────

DROP TABLE IF EXISTS temp_closest_ways;

CREATE TEMP TABLE temp_closest_ways ON COMMIT DROP AS
WITH split_addresses AS (
  SELECT b.id,
         a.city,
         a.country,
         a.street AS original_street,
         unnest(string_to_array(a.street, ';')) AS individual_street
  FROM {output_schema}.buildings b
  JOIN property p ON b.id = p.feature_id
  JOIN address  a ON p.val_address_id = a.id
),
building_addresses AS (
  SELECT id AS building_id,
         regexp_replace(trim(individual_street), '\s*\d+[\w,]*$', '') AS street,
         (regexp_match(trim(individual_street), '\s*(\d+[\w,]*)$'))[1] AS number,
         city,
         country,
         original_street
  FROM split_addresses
)
SELECT DISTINCT ON (ba.building_id)
       ba.building_id,
       w.way_id AS way_id_by_address
FROM building_addresses       AS ba
JOIN {output_schema}.buildings AS b
  ON ba.building_id = b.id
JOIN {output_schema}.ways AS w
  ON ba.street = w.name OR ba.street = w.name_kurz
ORDER BY ba.building_id, b.centroid <-> w.geom;

-- ─────────────────────────────────────────────
-- 3) APPLY THE UPDATE
-- ─────────────────────────────────────────────

UPDATE {output_schema}.buildings AS b
SET address_street_id = t.way_id_by_address
FROM temp_closest_ways AS t
WHERE b.id = t.building_id;

-- Cleanup temporary table
DROP TABLE IF EXISTS temp_closest_ways;