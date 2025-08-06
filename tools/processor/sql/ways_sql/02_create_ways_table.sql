/*
═══════════════════════════════════════════════════════════════════════════════
                         WAYS TABLE INITIALIZATION SCRIPT
═══════════════════════════════════════════════════════════════════════════════

PURPOSE:
--------
This script defines the core table for storing processed street/way geometries 
and attributes relevant for routing, spatial analysis, and building-to-street
assignment operations.

TABLE OVERVIEW:
---------------
{output_schema}.ways:
- Stores simplified and filtered road network data derived from base mapping sources
- Includes routing-relevant metadata such as source/target node IDs and traversal costs
- Encodes geometries as EPSG:3035-projected LineStrings, suitable for accurate
  distance-based spatial operations

COLUMN DESCRIPTIONS:
--------------------
- way_id: Unique identifier for each street segment (auto-incremented)
- verkehrslinie_id_basemap: Original street identifier from the basemap
- clazz: Integer-encoded road classification (e.g., highway, residential)
- source/target: Node identifiers for graph-based routing algorithms
- cost/reverse_cost: Forward and backward traversal costs (e.g., time or distance)
- geom: LineString geometry representing the road segment
- postcode: Integer postal code associated with the street segment (optional)

COORDINATE SYSTEM:
------------------
- EPSG:3035 – Projected European coordinate system used for accurate distance
  and proximity calculations.

═══════════════════════════════════════════════════════════════════════════════
*/

CREATE TABLE IF NOT EXISTS {output_schema}.ways (
    way_id                         SERIAL PRIMARY KEY,
    verkehrslinie_id_basemap  TEXT,
    clazz                      INTEGER,
    source                     INTEGER,
    target                     INTEGER,
    cost                       DOUBLE PRECISION,
    reverse_cost               DOUBLE PRECISION,
    geom                       geometry(LineString, 3035),
    postcode                 INTEGER
);

/*
═══════════════════════════════════════════════════════════════════════════════
                            INDEX CREATION SECTION
═══════════════════════════════════════════════════════════════════════════════

PURPOSE:
--------
These indexes support efficient spatial operations, filtering, and joining with
external datasets (e.g., basemap or building data). They are critical for
performance in both preprocessing and query-time execution.

INDEX EXPLANATIONS:
-------------------
- idx_ways_geom: Enables fast spatial queries (e.g., nearest neighbor, intersections)
- idx_ways_verkehrslinie_id: Optimizes joins using basemap IDs (e.g., for enrichment)
- idx_verkehrslinie_id: Index on raw input data to support joins when filling `ways`

═══════════════════════════════════════════════════════════════════════════════
*/

CREATE INDEX IF NOT EXISTS idx_ways_geom ON {output_schema}.ways USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_ways_verkehrslinie_id ON {output_schema}.ways (verkehrslinie_id_basemap);
CREATE INDEX IF NOT EXISTS idx_verkehrslinie_id ON {input_schema}.bmp_verkehrslinie (id);

