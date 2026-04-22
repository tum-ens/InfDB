-- ============================================================
-- Temporary tables for road segments and connection line segments
--
-- Notes:
-- - Build `ways_tem` from basemap_verkehrslinie intersecting the `{ags}` boundary
-- - Keep one LINESTRING part per source feature (longest)
-- - Add common enrichment / length columns used later in the pipeline
-- - Create indexes for spatial predicates and key lookups
-- - Create empty `connection_lines_tem` with the same core columns as `ways_tem`
-- ============================================================

DROP TABLE IF EXISTS ways_tem; -- ensure clean temp table for this session

CREATE TEMP TABLE ways_tem AS
WITH src AS (
  SELECT
    v.ogc_fid::text AS src_id,          -- source feature id as text
    v.klasse,                           -- feature class
    v.objektart,                        -- feature type
    v.geom,                             -- source geometry (may be multi-part)
    g.ags::text AS ags                  -- municipality/region id (AGS) as text
  FROM {input_schema}.basemap_verkehrslinie v
  JOIN {input_schema}.bkg_vg5000_gem g
    ON g.ags = '{ags}'                  -- restrict to target AGS
   AND ST_Within(ST_Centroid(v.geom), g.geom)    -- keep features whose centroid is within the AGS polygon
),
dumped AS (
  SELECT
    src_id,                                             -- stable id carried through CTEs
    klasse,                                             -- keep classification for downstream mapping
    objektart,                                          -- keep type for downstream filtering/debug
    ags,                                                -- propagate AGS to output rows
    ST_SetSRID((ST_Dump(geom)).geom, ST_SRID(geom)) AS geom_part -- explode into parts and preserve SRID
  FROM src
),
ranked AS (
  SELECT
    src_id,                                             -- group key for selecting one part per feature
    klasse,
    objektart,
    ags,
    geom_part,
    -- pick exactly one part per src_id
    row_number() OVER (PARTITION BY src_id ORDER BY ST_Length(geom_part) DESC) AS rn -- longest part first
  FROM dumped
  WHERE geom_part IS NOT NULL                  -- exclude NULL parts
    AND NOT ST_IsEmpty(geom_part)              -- exclude empty geometries
    AND GeometryType(geom_part) = 'LINESTRING' -- keep only LINESTRING parts
)
SELECT
  src_id AS id,                      -- output id (text) used as the stable road segment key
  klasse,                            -- preserved road class attribute
  objektart,                         -- preserved feature type attribute
  geom_part AS geom,                 -- chosen LINESTRING geometry (single part per id)
  ags                                -- AGS tag for downstream scoping
FROM ranked
WHERE rn = 1;                        -- keep only the top-ranked part per src_id

ALTER TABLE ways_tem
  ADD COLUMN IF NOT EXISTS postcode integer;  -- filled later after postcode enrichment/join

ALTER TABLE ways_tem
  ADD COLUMN IF NOT EXISTS length_geo double precision
    GENERATED ALWAYS AS (ST_Length(geom)) STORED; -- geometric length of the segment (native SRID units)

ALTER TABLE ways_tem
  ADD COLUMN IF NOT EXISTS length_filter double precision; -- length accumulator used in merge/delete bookkeeping

ALTER TABLE ways_tem
  ADD COLUMN IF NOT EXISTS length_connection_line double precision; -- length accumulator used for connection line accounting

CREATE INDEX IF NOT EXISTS ways_tem_geom_gix ON ways_tem USING gist (geom); -- spatial predicates (intersects/within/nn)
CREATE INDEX IF NOT EXISTS ways_tem_id_bix ON ways_tem (id);               -- id lookup/join index
CREATE INDEX IF NOT EXISTS ways_tem_ags_bix ON ways_tem (ags);             -- AGS scoped filtering



DROP TABLE IF EXISTS connection_lines_tem; -- ensure clean temp table for this session

CREATE TEMP TABLE connection_lines_tem (
    ags text,                               -- AGS tag for downstream scoping
    id text,                                -- stable segment id / connection line id
    connected_way_id text,                  -- id of the way in ways_tem this connection belongs to
    klasse text,                            -- preserved class attribute
    objektart text,                         -- preserved type attribute
    geom geometry,                          -- geometry column with same general type style as existing table

    postcode integer,                       -- filled later after postcode enrichment/join
    length_geo double precision GENERATED ALWAYS AS (ST_Length(geom)) STORED, -- geometric length of the segment
    length_filter double precision,         -- length accumulator used in merge/delete bookkeeping
    length_connection_line double precision -- length accumulator used for connection line accounting
);

CREATE INDEX IF NOT EXISTS connection_lines_tem_geom_gix ON connection_lines_tem USING gist (geom); -- spatial predicates (intersects/within/nn)
CREATE INDEX IF NOT EXISTS connection_lines_tem_id_bix ON connection_lines_tem (id);               -- id lookup/join index
CREATE INDEX IF NOT EXISTS connection_lines_tem_ags_bix ON connection_lines_tem (ags);             -- AGS scoped filtering
CREATE INDEX IF NOT EXISTS connection_lines_tem_connected_way_id_bix ON connection_lines_tem (connected_way_id); -- connected way lookup/join index