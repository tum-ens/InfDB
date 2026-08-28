-- ============================================================
-- 06_z_fill_mixed_use.sql
-- Splits every building into a residential and a non-residential
-- floor-area component and promotes mixed-use buildings.
--
-- WHY THIS EXISTS
--   LOD2 carries exactly one function code per building and no secondary
--   usage attribute, so a building with shops on the ground floor and flats
--   above is labelled either fully Residential or fully Commercial. Census
--   occupants are then allocated to Residential buildings only, which
--   over-concentrates population in the residential-only stock and leaves
--   population in cells without a Residential building unassigned.
--
-- WHAT THIS SCRIPT PRODUCES
--   temp_buildings.residential_floor_area     residential component  [m2]
--   temp_buildings.nonresidential_floor_area  commercial/public component [m2]
--   temp_buildings.building_use = 'Mixed'     for promoted buildings
--   temp_buildings.mix_score / mix_rule / mix_confidence  provenance
--
--   The two components always add up to the gross floor area
--   (floor_area * floor_number). 07 and 08 allocate census occupants and
--   households on the residential component only.
--
-- ------------------------------------------------------------
-- STEP 1 - EVIDENCE
--   No source states mixed use directly: OSM's building:use / building:flats
--   tags are effectively unused in Germany and LOD2 has no second function.
--   Mixed use is therefore inferred from independent indirect signals:
--
--     osm_residential      OSM tags the footprint residential/apartments
--                          while LOD2 calls it commercial. The two sources
--                          disagree, which is the strongest single signal.
--     has_address          The footprint carries a street address. Addresses
--                          mark buildings people live or work in; sheds,
--                          garages and barns do not get one (measured in
--                          Sonthofen: 94% of residential buildings have an
--                          address, 25% of commercial ones).
--     in_mixed_area        Inside an official ATKIS mixed-use settlement area
--                          (FlaecheGemischterNutzung). OSM has no equivalent.
--     in_residential_area  Inside a residential settlement area, weaker
--                          context-only evidence.
--     in_industrial_area   Inside an industrial/commercial settlement area.
--                          Negative evidence: a warehouse on an industrial
--                          estate is very unlikely to contain dwellings.
--     has_business_poi     A shop, restaurant or office point falls inside the
--                          footprint. Used in both directions: it supports
--                          mixed use in a commercial building and marks a
--                          commercial ground floor in a residential one.
--     is_institutional     Inside a social/education/health/religious area.
--                          Such buildings (dormitories, care homes, staff
--                          housing) do contain dwellings but are not
--                          shop-below/flats-above buildings, so they get their
--                          own floor-area rule in step 5.
--
--   Every evidence source is optional. Where a source is not imported the
--   corresponding flags stay false and the script degrades gracefully.
--
-- STEP 2 - SCORE
--   The flags are combined into a single score with configurable weights.
--   Only Commercial and Public buildings with at least the configured number
--   of storeys can score; a mixed-use building needs more than one floor.
--
-- STEP 3 - QUOTA
--   Evidence says which buildings are plausible, not how many are real, and
--   OSM coverage is too uneven to trust a count. The census supplies the
--   count: zensus_2022_100m_gebaeude_typ_groesse.anderergebaeudetyp reports
--   per cell how many buildings contain dwellings without being classic one-,
--   two- or multi-family houses. Read directly from {input_schema} because
--   06_prepare_grid only fills the grid table at the configured
--   census_building_type_resolution, which may be 1km.
--
--   The quota is treated as an upper bound, not a target: it also covers
--   dormitories and care homes, and the census perturbs small counts with the
--   Cell-Key method, so component values do not necessarily sum to the total.
--
-- STEP 4 - PROMOTION
--   Quota rule    within a cell, take the highest scoring candidates above the
--                 score threshold, at most as many as the quota allows.
--   Rescue rule   a cell with census population but no residential building at
--                 all cannot have its population allocated anywhere. Such
--                 cells promote their best candidates regardless of quota,
--                 because those residents demonstrably live somewhere. A
--                 separate, lower score threshold applies; cells that reach
--                 neither threshold stay unresolved rather than being filled
--                 with a guess.
--
-- STEP 5 - FLOOR-AREA SPLIT
--   No source measures the split: OSM building:levels covers ~3% of buildings
--   and building:flats none, so only the LOD2 storey count is available. The
--   split therefore rests on a structural assumption, recorded per building in
--   mix_rule so it can be replaced later:
--
--     institutional      residential share 1.0, no commercial floor. These are
--                        residential buildings that LOD2 mislabelled.
--     pedestrian         commercial ground floor plus first upper floor.
--                        In prime retail locations (1a-Lage) retail extends
--                        above the ground floor. Proximity to an ATKIS
--                        Fussgaengerzone is used as the location proxy.
--     standard           commercial ground floor, residential above.
--     ground_floor_shop  a Residential building containing a business POI;
--                        its ground floor moves to the commercial component.
--     full_residential / full_nonresidential  unchanged single-use buildings.
--
--   The resulting share is clamped to the configured band. German real-estate
--   practice classifies a building as a Wohn- und Geschaeftshaus only while
--   the commercial share stays between 20% and 80%; outside that band a
--   building is single-use with a subordinate secondary use. The clamp also
--   prevents the two-commercial-floor rule from driving a two-storey building
--   to zero residential area.
-- ============================================================

-- ------------------------------------------------------------
-- STEP 1: evidence
-- ------------------------------------------------------------
-- Bounding box of the AGS currently processed. Evidence layers carry no
-- gemeindeschluessel, so they are clipped to this box in their own SRID:
-- with one worker per AGS nobody may scan the nationwide layer.
DROP TABLE IF EXISTS temp_mix_extent;
CREATE TEMP TABLE temp_mix_extent AS
SELECT ST_Expand(ST_SetSRID(ST_Extent(geom)::geometry, {EPSG}),
                 {mu_pedestrian_buffer_m}) AS geom
FROM temp_buildings;

DROP TABLE IF EXISTS temp_mix_evidence;
CREATE TEMP TABLE temp_mix_evidence AS
SELECT b.id,
       b.building_use,
       b.floor_area,
       b.floor_number,
       b.height,
       b.geom,
       b.centroid,
       false AS osm_residential,
       false AS has_address,
       false AS has_business_poi,
       false AS in_mixed_area,
       false AS in_residential_area,
       false AS in_industrial_area,
       false AS is_institutional,
       false AS near_pedestrian_zone
FROM temp_buildings b;

CREATE INDEX ON temp_mix_evidence (id);
CREATE INDEX ON temp_mix_evidence USING GIST (geom);
CREATE INDEX ON temp_mix_evidence USING GIST (centroid);

-- OSM footprint attributes: the polygon covering the largest share of the
-- LOD2 footprint wins, above the configured overlap threshold.
DO $$
DECLARE
    src_srid   int;
    scope_geom geometry;
BEGIN
    IF to_regclass('{input_schema}.osm_building_polygon') IS NULL THEN
        RAISE NOTICE '[MixedUse] osm_building_polygon not present - OSM evidence skipped';
        RETURN;
    END IF;

    SELECT ST_SRID(geom) INTO src_srid FROM {input_schema}.osm_building_polygon LIMIT 1;
    IF src_srid IS NULL THEN
        RAISE NOTICE '[MixedUse] osm_building_polygon empty - OSM evidence skipped';
        RETURN;
    END IF;
    scope_geom := ST_Transform((SELECT geom FROM temp_mix_extent), src_srid);

    DROP TABLE IF EXISTS temp_mix_osm;
    CREATE TEMP TABLE temp_mix_osm AS
    SELECT o.osm_subtype,
           o.housenumber,
           ST_Transform(o.geom, {EPSG}) AS geom
    FROM {input_schema}.osm_building_polygon o
    WHERE o.geom && scope_geom;
    CREATE INDEX ON temp_mix_osm USING GIST (geom);

    UPDATE temp_mix_evidence e
    SET osm_residential = (m.osm_subtype IN ('residential', 'apartments', 'house', 'detached',
                                             'terrace', 'semidetached_house', 'dormitory')),
        has_address     = (m.housenumber IS NOT NULL)
    FROM (
        SELECT c.id, o.osm_subtype, o.housenumber
        FROM temp_mix_evidence c
        CROSS JOIN LATERAL (
            SELECT o.osm_subtype, o.housenumber
            FROM temp_mix_osm o
            WHERE o.geom && c.geom
              AND ST_Area(ST_Intersection(c.geom, o.geom)) / NULLIF(ST_Area(c.geom), 0) >= {mu_min_overlap}
            ORDER BY ST_Area(ST_Intersection(c.geom, o.geom)) DESC
            LIMIT 1
        ) o
    ) m
    WHERE e.id = m.id;

    DROP TABLE IF EXISTS temp_mix_osm;
END $$;

-- Business points of interest inside the footprint.
DO $$
DECLARE
    src_srid   int;
    scope_geom geometry;
BEGIN
    IF to_regclass('{input_schema}.osm_poi_point') IS NULL
       OR to_regclass('{input_schema}.osm_poi_polygon') IS NULL THEN
        RAISE NOTICE '[MixedUse] osm_poi tables not present - POI evidence skipped';
        RETURN;
    END IF;

    SELECT ST_SRID(geom) INTO src_srid FROM {input_schema}.osm_poi_point LIMIT 1;
    IF src_srid IS NULL THEN
        RAISE NOTICE '[MixedUse] osm_poi_point empty - POI evidence skipped';
        RETURN;
    END IF;
    scope_geom := ST_Transform((SELECT geom FROM temp_mix_extent), src_srid);

    DROP TABLE IF EXISTS temp_mix_poi;
    CREATE TEMP TABLE temp_mix_poi AS
    SELECT ST_Transform(geom, {EPSG}) AS geom
    FROM {input_schema}.osm_poi_point
    WHERE geom && scope_geom
    UNION ALL
    SELECT ST_PointOnSurface(ST_Transform(geom, {EPSG}))
    FROM {input_schema}.osm_poi_polygon
    WHERE geom && scope_geom;
    CREATE INDEX ON temp_mix_poi USING GIST (geom);

    UPDATE temp_mix_evidence e
    SET has_business_poi = true
    WHERE EXISTS (
        SELECT 1 FROM temp_mix_poi p
        WHERE p.geom && e.geom AND ST_Contains(e.geom, p.geom)
    );

    DROP TABLE IF EXISTS temp_mix_poi;
END $$;

-- ATKIS settlement areas: land-use context and the institutional flag.
DO $$
DECLARE
    src_srid   int;
    scope_geom geometry;
BEGIN
    IF to_regclass('{input_schema}.basemap_siedlungsflaeche') IS NULL THEN
        RAISE NOTICE '[MixedUse] basemap_siedlungsflaeche not present - land-use evidence skipped';
        RETURN;
    END IF;

    SELECT ST_SRID(geom) INTO src_srid FROM {input_schema}.basemap_siedlungsflaeche LIMIT 1;
    IF src_srid IS NULL THEN
        RAISE NOTICE '[MixedUse] basemap_siedlungsflaeche empty - land-use evidence skipped';
        RETURN;
    END IF;
    scope_geom := ST_Transform((SELECT geom FROM temp_mix_extent), src_srid);

    DROP TABLE IF EXISTS temp_mix_landuse;
    CREATE TEMP TABLE temp_mix_landuse AS
    SELECT objektart,
           klasse,
           ST_Transform(geom, {EPSG}) AS geom
    FROM {input_schema}.basemap_siedlungsflaeche
    WHERE geom && scope_geom;
    CREATE INDEX ON temp_mix_landuse USING GIST (geom);

    UPDATE temp_mix_evidence e
    SET in_mixed_area       = (l.objektart = 'FlaecheGemischterNutzung'),
        in_residential_area = (l.objektart = 'Wohnbauflaeche'),
        in_industrial_area  = (l.objektart = 'IndustrieUndGewerbeflaeche'),
        is_institutional    = (l.objektart = 'FlaecheBesondererFunktionalerPraegung'
                               AND l.klasse IN ('Soziales', 'Bildung und Wissenschaft',
                                                'Gesundheit, Kur', 'Religiöse Einrichtung'))
    FROM (
        SELECT c.id, a.objektart, a.klasse
        FROM temp_mix_evidence c
        CROSS JOIN LATERAL (
            SELECT l.objektart, l.klasse
            FROM temp_mix_landuse l
            WHERE l.geom && c.centroid AND ST_Contains(l.geom, c.centroid)
            LIMIT 1
        ) a
    ) l
    WHERE e.id = l.id;

    DROP TABLE IF EXISTS temp_mix_landuse;
END $$;

-- Pedestrian zone proximity, used as the prime-retail-location proxy.
DO $$
DECLARE
    src_srid   int;
    scope_geom geometry;
BEGIN
    IF to_regclass('{input_schema}.basemap_verkehrslinie') IS NULL THEN
        RAISE NOTICE '[MixedUse] basemap_verkehrslinie not present - pedestrian zone evidence skipped';
        RETURN;
    END IF;

    SELECT ST_SRID(geom) INTO src_srid FROM {input_schema}.basemap_verkehrslinie LIMIT 1;
    IF src_srid IS NULL THEN
        RAISE NOTICE '[MixedUse] basemap_verkehrslinie empty - pedestrian zone evidence skipped';
        RETURN;
    END IF;
    scope_geom := ST_Transform((SELECT geom FROM temp_mix_extent), src_srid);

    DROP TABLE IF EXISTS temp_mix_pedestrian;
    CREATE TEMP TABLE temp_mix_pedestrian AS
    SELECT ST_Transform(geom, {EPSG}) AS geom
    FROM {input_schema}.basemap_verkehrslinie
    WHERE funktion_name = 'Fußgängerzone'
      AND geom && scope_geom;
    CREATE INDEX ON temp_mix_pedestrian USING GIST (geom);

    UPDATE temp_mix_evidence e
    SET near_pedestrian_zone = true
    WHERE EXISTS (
        SELECT 1 FROM temp_mix_pedestrian f
        WHERE ST_DWithin(e.geom, f.geom, {mu_pedestrian_buffer_m})
    );

    DROP TABLE IF EXISTS temp_mix_pedestrian;
END $$;

-- ------------------------------------------------------------
-- STEP 2: score
-- ------------------------------------------------------------
DROP TABLE IF EXISTS temp_mix_candidates;
CREATE TEMP TABLE temp_mix_candidates AS
SELECT e.id,
       e.floor_area,
       e.floor_number,
       e.height,
       e.centroid,
       e.is_institutional,
         (CASE WHEN e.osm_residential     THEN {mu_w_osm_residential}  ELSE 0 END)
       + (CASE WHEN e.in_mixed_area       THEN {mu_w_mixed_area}       ELSE 0 END)
       + (CASE WHEN e.has_address         THEN {mu_w_address}          ELSE 0 END)
       + (CASE WHEN e.in_residential_area THEN {mu_w_residential_area} ELSE 0 END)
       + (CASE WHEN e.floor_number >= 3   THEN {mu_w_floors_3plus}     ELSE 0 END)
       + (CASE WHEN e.in_industrial_area  THEN {mu_w_industrial_area}  ELSE 0 END) AS score
FROM temp_mix_evidence e
WHERE '{mu_status}' = 'active'
  AND e.building_use IN ('Commercial', 'Public')
  AND e.floor_number >= {mu_min_floors};

CREATE INDEX ON temp_mix_candidates (id);
CREATE INDEX ON temp_mix_candidates USING GIST (centroid);

-- ------------------------------------------------------------
-- STEP 3: census quota per 100m cell
-- ------------------------------------------------------------
DROP TABLE IF EXISTS temp_mix_cells;
CREATE TEMP TABLE temp_mix_cells AS
SELECT g.id                              AS cell_id,
       g.geom,
       COALESCE(g.einwohner, 0)          AS einwohner,
       COALESCE(z.anderergebaeudetyp, 0) AS quota
FROM temp_buildings_grid_100m g
LEFT JOIN {input_schema}.zensus_2022_100m_gebaeude_typ_groesse z
       ON z.x_mp_100m = g.x_mp AND z.y_mp_100m = g.y_mp;

CREATE INDEX ON temp_mix_cells USING GIST (geom);

-- ------------------------------------------------------------
-- STEP 4: promotion
-- ------------------------------------------------------------
DROP TABLE IF EXISTS temp_mix_ranked;
CREATE TEMP TABLE temp_mix_ranked AS
SELECT c.id,
       c.score,
       c.is_institutional,
       g.cell_id,
       g.quota,
       g.einwohner,
       ROW_NUMBER() OVER (PARTITION BY g.cell_id
                          ORDER BY c.score DESC, c.floor_area * c.height DESC) AS rank_in_cell
FROM temp_mix_candidates c
JOIN temp_mix_cells g
  ON c.centroid && g.geom AND ST_Contains(g.geom, c.centroid);

CREATE INDEX ON temp_mix_ranked (cell_id);

-- Cells holding census population but no residential building at all.
DROP TABLE IF EXISTS temp_mix_unserved_cells;
CREATE TEMP TABLE temp_mix_unserved_cells AS
SELECT g.cell_id
FROM temp_mix_cells g
WHERE g.einwohner > 0
  AND NOT EXISTS (
      SELECT 1
      FROM temp_buildings b
      WHERE b.building_use = 'Residential'
        AND b.centroid && g.geom
        AND ST_Contains(g.geom, b.centroid)
  );

DROP TABLE IF EXISTS temp_mix_promoted;
CREATE TEMP TABLE temp_mix_promoted AS
SELECT id, MIN(score) AS score, bool_or(is_institutional) AS is_institutional, MIN(rule) AS rule
FROM (
    SELECT r.id, r.score, r.is_institutional, 'quota' AS rule
    FROM temp_mix_ranked r
    WHERE r.score >= {mu_threshold}
      AND r.rank_in_cell <= r.quota
    UNION ALL
    SELECT r.id, r.score, r.is_institutional, 'rescue'
    FROM temp_mix_ranked r
    JOIN temp_mix_unserved_cells u ON u.cell_id = r.cell_id
    WHERE r.score >= {mu_rescue_threshold}
      AND r.rank_in_cell <= {mu_rescue_max_per_cell}
) p
GROUP BY id;

CREATE INDEX ON temp_mix_promoted (id);

UPDATE temp_buildings b
SET building_use   = 'Mixed',
    mix_score      = p.score,
    mix_confidence = CASE WHEN p.rule = 'rescue' THEN 'low'
                          WHEN p.score >= {mu_threshold} + {mu_w_address} THEN 'high'
                          ELSE 'medium' END
FROM temp_mix_promoted p
WHERE b.id = p.id;

-- ------------------------------------------------------------
-- STEP 5: floor-area split
-- ------------------------------------------------------------
DROP TABLE IF EXISTS temp_mix_share;
CREATE TEMP TABLE temp_mix_share AS
WITH classified AS (
    SELECT b.id,
           b.floor_area,
           b.floor_number,
           b.building_use,
           CASE
               WHEN b.building_use = 'Mixed' AND p.is_institutional              THEN 'institutional'
               WHEN b.building_use = 'Mixed' AND e.near_pedestrian_zone          THEN 'pedestrian'
               WHEN b.building_use = 'Mixed'                                     THEN 'standard'
               WHEN b.building_use = 'Residential' AND e.has_business_poi
                    AND b.floor_number >= 2 AND '{mu_status}' = 'active'         THEN 'ground_floor_shop'
               WHEN b.building_use = 'Residential'                               THEN 'full_residential'
               ELSE 'full_nonresidential'
           END AS rule
    FROM temp_buildings b
    JOIN temp_mix_evidence e ON e.id = b.id
    LEFT JOIN temp_mix_promoted p ON p.id = b.id
),
commercial_floors AS (
    SELECT c.*,
           CASE c.rule
               WHEN 'institutional'      THEN 0
               WHEN 'pedestrian'         THEN {mu_commercial_floors_pedestrian}
               WHEN 'standard'           THEN {mu_commercial_floors_default}
               WHEN 'ground_floor_shop'  THEN {mu_commercial_floors_default}
               WHEN 'full_residential'   THEN 0
               ELSE c.floor_number
           END AS commercial_floors
    FROM classified c
)
SELECT id,
       rule,
       floor_area * floor_number AS gross_floor_area,
       CASE
           WHEN rule = 'full_residential' OR rule = 'institutional' THEN 1.0
           WHEN rule = 'full_nonresidential'                        THEN 0.0
           ELSE LEAST(GREATEST((floor_number - commercial_floors)::double precision
                               / NULLIF(floor_number, 0),
                               {mu_min_residential_share}),
                      {mu_max_residential_share})
       END AS residential_share
FROM commercial_floors;

CREATE INDEX ON temp_mix_share (id);

UPDATE temp_buildings b
SET residential_floor_area    = s.gross_floor_area * s.residential_share,
    nonresidential_floor_area = s.gross_floor_area * (1 - s.residential_share),
    mix_rule                  = s.rule
FROM temp_mix_share s
WHERE b.id = s.id;

-- release memory
DROP TABLE IF EXISTS temp_mix_candidates;
DROP TABLE IF EXISTS temp_mix_cells;
DROP TABLE IF EXISTS temp_mix_ranked;
DROP TABLE IF EXISTS temp_mix_unserved_cells;
DROP TABLE IF EXISTS temp_mix_promoted;
DROP TABLE IF EXISTS temp_mix_share;
DROP TABLE IF EXISTS temp_mix_evidence;
DROP TABLE IF EXISTS temp_mix_extent;