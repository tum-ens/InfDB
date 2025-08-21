/*
═══════════════════════════════════════════════════════════════════════════════
                    STREET NETWORK IMPORT & COST CALCULATION
═══════════════════════════════════════════════════════════════════════════════

PURPOSE:
--------
This script imports street segment data (`bmp_verkehrslinie`) from the basemap 
dataset into the working schema's `ways` table, calculates routing costs, and 
assigns directional constraints for one-way and two-way streets.

ALGORITHM OVERVIEW:
-------------------
1. Filter out non-routable classes (e.g., class 99)
2. Transform all geometries to EPSG:3035 (ETRS89 / LAEA Europe)
3. Calculate routing cost as:  
      cost = (segment length in km) / (class-based speed in km/h)
4. Use traffic direction info to assign appropriate `reverse_cost`:
    - High penalty (1,000,000) for one-way restricted segments
    - Equal to forward cost for bidirectional or undefined direction

INPUT REQUIREMENTS:
-------------------
- bmp_verkehrslinie (from {input_schema}): Basemap streets with geometry, class, and direction
- map_strasse_klasse_to_class_kmh(): Mapping function returning routing class and speed

OUTPUT:
-------
- Inserts processed data into {output_schema}.ways table
- Updates reverse_cost field based on allowed traffic direction


COORDINATE SYSTEM:
------------------
All geometries are transformed to EPSG:3035 for consistency with other layers

═══════════════════════════════════════════════════════════════════════════════
*/

-- ─────────────────────────────────────────────
-- 1. INSERT ROUTABLE ROAD SEGMENTS WITH COSTS
-- ─────────────────────────────────────────────

INSERT INTO {output_schema}.ways (
    verkehrslinie_id_basemap,
    clazz,
    geom,
    cost
)
SELECT
    v.id AS verkehrslinie_id_basemap,
    c.clazz,
    ST_Transform(v.geometry, 3035) AS geom, 
    ST_Length(ST_Transform(v.geometry, 3035)) / 1000.0 / NULLIF(c.kmh, 0) AS cost
FROM {input_schema}.bmp_verkehrslinie v,
     LATERAL {output_schema}.map_strasse_klasse_to_class_kmh(v.klasse) AS c
WHERE v.geometry IS NOT NULL AND c.clazz NOT IN (99);

-- ─────────────────────────────────────────────
-- 2. SET REVERSE COST BASED ON TRAFFIC DIRECTION
-- ─────────────────────────────────────────────

UPDATE {output_schema}.ways AS w
SET reverse_cost = 
  CASE 
    WHEN v.richtung = '1' THEN 1000000.0  -- one-way
    WHEN v.richtung = '0' OR v.richtung IS NULL THEN w.cost  -- bidirectional
  END
FROM {input_schema}.bmp_verkehrslinie AS v
WHERE w.verkehrslinie_id_basemap = v.id;
