-- ============================================================
-- 06_z_fill_mixed_use.sql
-- Splits every building into a residential and a non-residential
-- floor-area component and promotes mixed-use buildings.
--
-- WHY THIS EXISTS
--   LOD2 carries exactly one function code per building and no secondary
--   usage attribute, so a building with shops on the ground floor and flats
--   above is usually labelled as a single use, either Residential or
--   Commercial. Census occupants are then allocated to Residential
--   buildings only, which leaves population in cells without a Residential
--   building unassigned.
--
--   Ground truth (a municipal building registry compared against LOD2 for
--   one town) shows that mislabelling runs in both directions, but LOD2's
--   Residential and Commercial labels agree with it well enough that they
--   are only reconsidered through the cell quota in STEP 4. The mislabelling
--   concentrates in one code, 31001_9998 ("function not specified"). LOD2's
--   code list does have mixed-use categories, but data providers use them
--   unevenly: some regions label a mixed building as plain Residential or
--   Commercial, others fall back to 31001_9998. The code therefore reflects
--   data quality rather than a building type.
--
-- WHAT THIS SCRIPT PRODUCES
--   temp_buildings.residential_floor_area     residential component  [m2]
--   temp_buildings.nonresidential_floor_area  commercial/public component [m2]
--   temp_buildings.building_use = 'Mixed'     for promoted buildings
--   temp_buildings.mix_exclusion_reason       why a candidate was left
--                                              Unknown, see STEP 3
--   temp_buildings.mix_rule                   floor-area split rule, STEP 5
--
--   The two components always add up to the gross floor area
--   (floor_area * floor_number). 07 and 08 allocate census occupants and
--   households on the residential component only.
--
--   Only promoted buildings carry both components, so a building with a
--   non-zero non-residential component is always labelled 'Mixed'. Buildings
--   LOD2 classifies as Residential or Commercial are left untouched, except
--   for the cell quota promotions of STEP 4.
--
-- ------------------------------------------------------------
-- STEP 1 - EVIDENCE
--   A 31001_9998 building is, overwhelmingly, a building LOD2's source data
--   simply failed to classify -- not a distinct architectural type. The
--   population is therefore treated as Mixed by default, and demoted back to
--   Unknown only when there is a specific, structural reason nobody could
--   live there:
--
--     in_industrial_area           Inside a basemap industrial/commercial
--                                  settlement area (IndustrieUndGewerbeflaeche).
--     in_cemetery                  Inside a basemap cemetery (Friedhof).
--     in_sport_leisure_area        Inside a basemap sport/leisure area
--                                  (SportFreizeitUndErholungsflaeche).
--     in_mining_area               Inside a basemap open-pit mine, quarry or
--                                  spoil heap (TagebauGrubeSteinbruch, Halde).
--     institutional_strict         Inside a basemap functional area classed
--                                  Kultur, Sicherheit und Ordnung, or
--                                  Regierung und Verwaltung -- museums,
--                                  fire/police stations, government offices.
--     health_spa_area              Inside a basemap functional area classed
--                                  Gesundheit, Kur or without a more specific
--                                  class -- hospitals, clinics, spa sites.
--     osm_nonresidential           OSM tags the footprint office, retail,
--                                  commercial, industrial, warehouse, kiosk
--                                  or supermarket.
--     osm_institutional_technical  OSM tags the footprint a school, hospital,
--                                  museum, government building, station or
--                                  other structurally non-residential use --
--                                  see the VALUES list in STEP 1 for the
--                                  full set.
--     osm_accommodation            OSM tags the footprint a hotel, or a hotel
--                                  point lies inside it.
--     osm_campus_amenity           Inside an OSM school, university, college,
--                                  hospital or clinic area.
--     osm_construction             OSM tags the footprint or its plot as under
--                                  construction (building or landuse).
--     osm_parking_transport        OSM tags the footprint a garage or bridge,
--                                  it lies in a parking area or railway
--                                  landuse, or a parking point lies inside it.
--     osm_service_building         OSM tags the footprint an insurance or
--                                  service building.
--     osm_education_site           Inside an OSM education landuse, or a
--                                  school, university, clinic, language school
--                                  or music school point lies inside it.
--     osm_culture_entertainment    A cinema, theatre, nightclub, event venue,
--                                  arts centre, gambling or gaming point lies
--                                  inside the footprint, or it is in a
--                                  theatre area.
--     osm_utility                  Inside an OSM substation, power plant or
--                                  utility area, or such a point lies inside
--                                  it.
--
--   Every evidence source is optional. Where a source is not imported the
--   corresponding flags stay false and the script degrades gracefully.
--
-- STEP 2 - VALIDATION
--   None of the flags above is trusted by assumption. Each is checked
--   against the buildings LOD2 already calls Residential in this AGS
--   (floor_number >= 2, the same population the split applies to): if the
--   flag also fires on more than {mu_max_false_positive_rate} of confirmed
--   housing stock here, it would throw away real residents and is dropped
--   for this AGS. What is left is a set of flags proven, in this specific
--   municipality, to essentially never coincide with a real dwelling.
--
-- STEP 3 - PROMOTION
--   A candidate is left Unknown if it carries at least one validated flag,
--   and promoted to Mixed otherwise. This is a deliberate change from an
--   earlier design that scored candidates against both a Residential and a
--   Commercial profile and promoted only above a joint threshold. That
--   approach under-promoted -- genuinely mixed buildings rarely score
--   strongly on both axes at once -- so the axis was dropped in favour of
--   excluding only what specific evidence rules out.
--
-- STEP 4 - CELL QUOTA
--   STEP 3 only ever promotes buildings LOD2 already left unclassified, so
--   it cannot fix a building Residential or Commercial mislabelling ran the
--   other way -- LOD2 calling a genuinely mixed building single-use. No
--   Zensus source counts mixed-use buildings directly (see the source notes
--   in STEP 4's queries below), but Zensus 2011's
--   sonstige_gebaeude_mit_wohnraum -- buildings with both residential and
--   non-residential floor space -- is a lower bound: a 100m cell cannot
--   hold fewer mixed-use buildings than the census counted there in 2011.
--
--   Where STEP 3 already met or exceeded that count in a cell, nothing more
--   happens there. Where it fell short, additional Residential/Commercial
--   buildings in the same cell (Public does not count) are promoted until
--   the count is met, preferring buildings touching an already-Mixed
--   building so growth reads as a contiguous block, then buildings nearest
--   to one where nothing touches, then a fixed pseudo-random selection
--   (ordered by a hash of the objectid, so it is repeatable) where the cell
--   had no Mixed building from STEP 3 to grow from at all. A cell with a
--   shortfall but no Residential/Commercial building left to promote stays
--   short -- there is nothing left to spend the quota on.
--
-- STEP 5 - FLOOR-AREA SPLIT
--   No source measures the split: OSM building:levels covers ~3% of buildings
--   and building:flats none, so only the LOD2 storey count is available. The
--   split therefore rests on a structural assumption, recorded per building in
--   mix_rule so it can be replaced later:
--
--     pedestrian         commercial ground floor plus first upper floor.
--                        In prime retail locations (1a-Lage) retail extends
--                        above the ground floor. Proximity to a basemap
--                        Fussgaengerzone is used as the location proxy.
--     standard           commercial ground floor, residential above.
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
       b.building_use_id,
       b.floor_area,
       b.floor_number,
       b.height,
       b.geom,
       b.centroid,
       false AS in_industrial_area,
       false AS in_cemetery,
       false AS in_sport_leisure_area,
       false AS in_mining_area,
       false AS institutional_strict,
       false AS health_spa_area,
       false AS osm_nonresidential,
       false AS osm_institutional_technical,
       false AS osm_accommodation,
       false AS osm_campus_amenity,
       false AS osm_construction,
       false AS osm_parking_transport,
       false AS osm_service_building,
       false AS osm_education_site,
       false AS osm_culture_entertainment,
       false AS osm_utility,
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
           ST_Transform(o.geom, {EPSG}) AS geom
    FROM {input_schema}.osm_building_polygon o
    WHERE o.geom && scope_geom;
    CREATE INDEX ON temp_mix_osm USING GIST (geom);

    UPDATE temp_mix_evidence e
    SET osm_nonresidential = (m.osm_subtype IN ('office', 'retail', 'commercial', 'industrial',
                                                 'warehouse', 'kiosk', 'supermarket')),
        osm_institutional_technical = (m.osm_subtype IN (
            'hospital', 'school', 'kindergarten', 'government', 'train_station', 'fire_station',
            'museum', 'university', 'college', 'storage_tank', 'hangar', 'barn', 'farm_auxiliary',
            'sports_hall', 'sports_centre', 'stadium', 'gymnasium', 'greenhouse', 'silo',
            'substation', 'transformer_tower', 'bunker', 'parking', 'parking_entrance',
            'church', 'chapel', 'mosque', 'synagogue', 'temple', 'shrine', 'monastery')),
        osm_accommodation     = (m.osm_subtype = 'hotel'),
        osm_construction      = (m.osm_subtype = 'construction'),
        osm_parking_transport = (m.osm_subtype IN ('garage', 'bridge')),
        osm_service_building  = (m.osm_subtype IN ('insurance', 'service'))
    FROM (
        SELECT c.id, o.osm_subtype
        FROM temp_mix_evidence c
        CROSS JOIN LATERAL (
            SELECT o.osm_subtype
            FROM temp_mix_osm o
            WHERE o.geom && c.geom
              -- half the LOD2 footprint: the two sources describe the same building
              AND ST_Area(ST_Intersection(c.geom, o.geom)) / NULLIF(ST_Area(c.geom), 0) >= 0.5
            ORDER BY ST_Area(ST_Intersection(c.geom, o.geom)) DESC
            LIMIT 1
        ) o
    ) m
    WHERE e.id = m.id;

    DROP TABLE IF EXISTS temp_mix_osm;
END $$;

-- OSM areas and points describing the function of the whole building or its
-- plot. A polygon applies when it holds the footprint centroid, or, for
-- polygons of building size, covers half the footprint; a point applies when
-- it lies inside the footprint.
DO $$
DECLARE
    src_srid   int;
    scope_geom geometry;
BEGIN
    DROP TABLE IF EXISTS temp_mix_osm_feature;
    CREATE TEMP TABLE temp_mix_osm_feature (flag text, is_area boolean, geom geometry);

    IF to_regclass('{input_schema}.osm_amenity_polygon') IS NOT NULL THEN
        SELECT ST_SRID(geom) INTO src_srid FROM {input_schema}.osm_amenity_polygon LIMIT 1;
        scope_geom := ST_Transform((SELECT geom FROM temp_mix_extent), src_srid);
        INSERT INTO temp_mix_osm_feature
        SELECT CASE WHEN osm_type IN ('school', 'university', 'college', 'hospital', 'clinic')
                         THEN 'osm_campus_amenity'
                    WHEN osm_type = 'parking' THEN 'osm_parking_transport'
                    ELSE 'osm_culture_entertainment' END,
               true, ST_MakeValid(ST_Transform(geom, {EPSG}))
        FROM {input_schema}.osm_amenity_polygon
        WHERE geom && scope_geom
          AND osm_type IN ('school', 'university', 'college', 'hospital', 'clinic', 'parking', 'theatre');
    END IF;

    IF to_regclass('{input_schema}.osm_landuse_polygon') IS NOT NULL THEN
        SELECT ST_SRID(geom) INTO src_srid FROM {input_schema}.osm_landuse_polygon LIMIT 1;
        scope_geom := ST_Transform((SELECT geom FROM temp_mix_extent), src_srid);
        INSERT INTO temp_mix_osm_feature
        SELECT CASE osm_type WHEN 'construction' THEN 'osm_construction'
                             WHEN 'railway'      THEN 'osm_parking_transport'
                             ELSE 'osm_education_site' END,
               true, ST_MakeValid(ST_Transform(geom, {EPSG}))
        FROM {input_schema}.osm_landuse_polygon
        WHERE geom && scope_geom
          AND osm_type IN ('construction', 'railway', 'education');
    END IF;

    IF to_regclass('{input_schema}.osm_infrastructure_polygon') IS NOT NULL THEN
        SELECT ST_SRID(geom) INTO src_srid FROM {input_schema}.osm_infrastructure_polygon LIMIT 1;
        scope_geom := ST_Transform((SELECT geom FROM temp_mix_extent), src_srid);
        INSERT INTO temp_mix_osm_feature
        SELECT 'osm_utility', true, ST_MakeValid(ST_Transform(geom, {EPSG}))
        FROM {input_schema}.osm_infrastructure_polygon
        WHERE geom && scope_geom
          AND ((osm_type = 'power' AND osm_subtype IN ('substation', 'plant')) OR osm_type = 'utility');
    END IF;

    IF to_regclass('{input_schema}.osm_poi_point') IS NOT NULL THEN
        SELECT ST_SRID(geom) INTO src_srid FROM {input_schema}.osm_poi_point LIMIT 1;
        scope_geom := ST_Transform((SELECT geom FROM temp_mix_extent), src_srid);
        INSERT INTO temp_mix_osm_feature
        SELECT 'osm_accommodation', false, ST_Transform(geom, {EPSG})
        FROM {input_schema}.osm_poi_point
        WHERE geom && scope_geom AND osm_type = 'tourism' AND osm_subtype = 'hotel';
    END IF;

    IF to_regclass('{input_schema}.osm_amenity_point') IS NOT NULL THEN
        SELECT ST_SRID(geom) INTO src_srid FROM {input_schema}.osm_amenity_point LIMIT 1;
        scope_geom := ST_Transform((SELECT geom FROM temp_mix_extent), src_srid);
        INSERT INTO temp_mix_osm_feature
        SELECT CASE WHEN osm_type IN ('school', 'university', 'clinic', 'language_school', 'music_school')
                         THEN 'osm_education_site'
                    WHEN osm_type = 'parking' THEN 'osm_parking_transport'
                    ELSE 'osm_culture_entertainment' END,
               false, ST_Transform(geom, {EPSG})
        FROM {input_schema}.osm_amenity_point
        WHERE geom && scope_geom
          AND osm_type IN ('school', 'university', 'clinic', 'language_school', 'music_school', 'parking',
                           'cinema', 'theatre', 'nightclub', 'events_venue', 'arts_centre', 'gambling');
    END IF;

    IF to_regclass('{input_schema}.osm_leisure_point') IS NOT NULL THEN
        SELECT ST_SRID(geom) INTO src_srid FROM {input_schema}.osm_leisure_point LIMIT 1;
        scope_geom := ST_Transform((SELECT geom FROM temp_mix_extent), src_srid);
        INSERT INTO temp_mix_osm_feature
        SELECT 'osm_culture_entertainment', false, ST_Transform(geom, {EPSG})
        FROM {input_schema}.osm_leisure_point
        WHERE geom && scope_geom AND osm_type IN ('adult_gaming_centre', 'dance');
    END IF;

    IF to_regclass('{input_schema}.osm_infrastructure_point') IS NOT NULL THEN
        SELECT ST_SRID(geom) INTO src_srid FROM {input_schema}.osm_infrastructure_point LIMIT 1;
        scope_geom := ST_Transform((SELECT geom FROM temp_mix_extent), src_srid);
        INSERT INTO temp_mix_osm_feature
        SELECT 'osm_utility', false, ST_Transform(geom, {EPSG})
        FROM {input_schema}.osm_infrastructure_point
        WHERE geom && scope_geom
          AND ((osm_type = 'power' AND osm_subtype IN ('substation', 'plant')) OR osm_type = 'utility');
    END IF;

    CREATE INDEX ON temp_mix_osm_feature USING GIST (geom);

    UPDATE temp_mix_evidence e
    SET osm_accommodation         = e.osm_accommodation         OR m.flags @> ARRAY['osm_accommodation'],
        osm_campus_amenity        = e.osm_campus_amenity        OR m.flags @> ARRAY['osm_campus_amenity'],
        osm_construction          = e.osm_construction          OR m.flags @> ARRAY['osm_construction'],
        osm_parking_transport     = e.osm_parking_transport     OR m.flags @> ARRAY['osm_parking_transport'],
        osm_education_site        = e.osm_education_site        OR m.flags @> ARRAY['osm_education_site'],
        osm_culture_entertainment = e.osm_culture_entertainment OR m.flags @> ARRAY['osm_culture_entertainment'],
        osm_utility               = e.osm_utility               OR m.flags @> ARRAY['osm_utility']
    FROM (
        SELECT c.id, array_agg(DISTINCT f.flag) AS flags
        FROM temp_mix_evidence c
        JOIN temp_mix_osm_feature f ON f.geom && c.geom
        WHERE (f.is_area AND (ST_Contains(f.geom, c.centroid)
                              OR (ST_Area(f.geom) < 5000
                                  AND ST_Area(ST_Intersection(c.geom, f.geom)) >= 0.5 * ST_Area(c.geom))))
           OR (NOT f.is_area AND ST_Contains(c.geom, f.geom))
        GROUP BY c.id
    ) m
    WHERE e.id = m.id;

    DROP TABLE IF EXISTS temp_mix_osm_feature;
END $$;

-- basemap settlement and functional areas.
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
    SET in_industrial_area    = (l.objektart = 'IndustrieUndGewerbeflaeche'),
        in_cemetery           = (l.objektart = 'Friedhof'),
        in_sport_leisure_area = (l.objektart = 'SportFreizeitUndErholungsflaeche'),
        in_mining_area        = (l.objektart IN ('TagebauGrubeSteinbruch', 'Halde')),
        institutional_strict  = (l.objektart = 'FlaecheBesondererFunktionalerPraegung'
                                 AND l.klasse IN ('Kultur', 'Sicherheit und Ordnung',
                                                   'Regierung und Verwaltung')),
        health_spa_area       = (l.objektart = 'FlaecheBesondererFunktionalerPraegung'
                                 AND l.klasse IN ('Gesundheit, Kur',
                                                   'Fläche besonderer funktionaler Prägung'))
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

-- Pedestrian zone proximity, used as the prime-retail-location proxy in STEP 4.
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
-- STEP 2: validation
-- ------------------------------------------------------------
-- False-positive rate of each candidate flag against this AGS's own
-- confirmed housing stock (LOD2 Residential, floor_number >= 2 to match the
-- population the flag will actually be applied to). A flag clears the bar
-- only if it essentially never coincides with a real dwelling here.
DROP TABLE IF EXISTS temp_mix_validation;
CREATE TEMP TABLE temp_mix_validation AS
WITH residential_pool AS (
    SELECT e.*
    FROM temp_mix_evidence e
    WHERE e.building_use = 'Residential' AND e.floor_number >= 2
), flags AS (
    SELECT flag, fires
    FROM residential_pool,
    LATERAL (VALUES
        ('in_industrial_area',          in_industrial_area),
        ('in_cemetery',                 in_cemetery),
        ('in_sport_leisure_area',       in_sport_leisure_area),
        ('in_mining_area',              in_mining_area),
        ('institutional_strict',        institutional_strict),
        ('health_spa_area',             health_spa_area),
        ('osm_nonresidential',          osm_nonresidential),
        ('osm_institutional_technical', osm_institutional_technical),
        ('osm_accommodation',           osm_accommodation),
        ('osm_campus_amenity',          osm_campus_amenity),
        ('osm_construction',            osm_construction),
        ('osm_parking_transport',       osm_parking_transport),
        ('osm_service_building',        osm_service_building),
        ('osm_education_site',          osm_education_site),
        ('osm_culture_entertainment',   osm_culture_entertainment),
        ('osm_utility',                 osm_utility)
    ) AS v(flag, fires)
)
SELECT flag,
       count(*) FILTER (WHERE fires)::double precision / GREATEST(count(*), 1) AS false_positive_rate,
       count(*) FILTER (WHERE fires)::double precision / GREATEST(count(*), 1)
           < {mu_max_false_positive_rate} AS trusted
FROM flags
GROUP BY flag;

CREATE INDEX ON temp_mix_validation (flag);

-- ------------------------------------------------------------
-- STEP 3: promotion
-- ------------------------------------------------------------
DROP TABLE IF EXISTS temp_mix_decision;
CREATE TEMP TABLE temp_mix_decision AS
WITH cand AS (
    SELECT e.*
    FROM temp_mix_evidence e
    WHERE '{mu_status}' = 'active'
      AND e.building_use = 'Unknown'
      -- the split is vertical, so a single-storey building has no floor to keep residential
      AND e.floor_number >= 2
), unpivoted AS (
    SELECT c.id, flag, fires
    FROM cand c,
    LATERAL (VALUES
        ('in_industrial_area',          c.in_industrial_area),
        ('in_cemetery',                 c.in_cemetery),
        ('in_sport_leisure_area',       c.in_sport_leisure_area),
        ('in_mining_area',              c.in_mining_area),
        ('institutional_strict',        c.institutional_strict),
        ('health_spa_area',             c.health_spa_area),
        ('osm_nonresidential',          c.osm_nonresidential),
        ('osm_institutional_technical', c.osm_institutional_technical),
        ('osm_accommodation',           c.osm_accommodation),
        ('osm_campus_amenity',          c.osm_campus_amenity),
        ('osm_construction',            c.osm_construction),
        ('osm_parking_transport',       c.osm_parking_transport),
        ('osm_service_building',        c.osm_service_building),
        ('osm_education_site',          c.osm_education_site),
        ('osm_culture_entertainment',   c.osm_culture_entertainment),
        ('osm_utility',                 c.osm_utility)
    ) AS v(flag, fires)
), reasons AS (
    SELECT u.id, string_agg(u.flag, ', ' ORDER BY u.flag) AS exclusion_reason
    FROM unpivoted u
    JOIN temp_mix_validation val ON val.flag = u.flag
    WHERE u.fires AND val.trusted
    GROUP BY u.id
)
SELECT c.id, r.exclusion_reason
FROM cand c
LEFT JOIN reasons r ON r.id = c.id;

CREATE INDEX ON temp_mix_decision (id);

DROP TABLE IF EXISTS temp_mix_promoted;
CREATE TEMP TABLE temp_mix_promoted AS
SELECT id
FROM temp_mix_decision
WHERE exclusion_reason IS NULL;

CREATE INDEX ON temp_mix_promoted (id);

UPDATE temp_buildings b
SET building_use = 'Mixed'
FROM temp_mix_promoted p
WHERE b.id = p.id;

-- Candidates left Unknown keep a record of which validated flag(s) stopped
-- their promotion, for inspection.
UPDATE temp_buildings b
SET mix_exclusion_reason = d.exclusion_reason
FROM temp_mix_decision d
WHERE b.id = d.id AND d.exclusion_reason IS NOT NULL;

-- ------------------------------------------------------------
-- STEP 4: cell quota
-- ------------------------------------------------------------
-- Every 100m cell that STEP 3 left short of its Zensus 2011
-- sonstige_gebaeude_mit_wohnraum count gets topped up from that cell's own
-- Residential/Commercial stock (Public excluded, floor_number >= 2 to match
-- the population STEP 3 draws from). Optional: where the source is not
-- imported no cell has a quota and this step is a no-op.
DO $$
BEGIN
    IF to_regclass('{input_schema}.zensus_2011_100m_gebaeude_art') IS NULL THEN
        RAISE NOTICE '[MixedUse] zensus_2011_100m_gebaeude_art not present - cell quota skipped';
        RETURN;
    END IF;

    -- Cells with a 2011 mixed-housing count and how many Mixed buildings
    -- STEP 3 already produced there.
    DROP TABLE IF EXISTS temp_mix_cell_state;
    CREATE TEMP TABLE temp_mix_cell_state AS
    SELECT g.id AS grid_id,
           g.geom,
           z.sonstige_gebaeude_mit_wohnraum AS quota,
           (SELECT count(*) FROM temp_buildings b
            WHERE b.building_use = 'Mixed' AND ST_Contains(g.geom, b.centroid)) AS mixed_count
    FROM temp_buildings_grid_100m g
    JOIN {input_schema}.zensus_2011_100m_gebaeude_art z
      ON z.x_mp_100m = g.x_mp AND z.y_mp_100m = g.y_mp
    WHERE z.sonstige_gebaeude_mit_wohnraum > 0;

    CREATE INDEX ON temp_mix_cell_state USING GIST (geom);

    -- Cells still short after STEP 3.
    DROP TABLE IF EXISTS temp_mix_shortfall;
    CREATE TEMP TABLE temp_mix_shortfall AS
    SELECT grid_id, geom, mixed_count, quota - mixed_count AS deficit
    FROM temp_mix_cell_state
    WHERE quota > mixed_count;

    CREATE INDEX ON temp_mix_shortfall USING GIST (geom);

    -- Rank each shortfall cell's Residential/Commercial pool: buildings
    -- touching an existing Mixed building first, then by distance to the
    -- nearest one, so growth reads as a contiguous block; cells with no
    -- Mixed seed at all rank by a hash of the objectid, since there is
    -- nothing to grow outward from. The hash gives an arbitrary but
    -- repeatable order, so every regeneration picks the same buildings.
    DROP TABLE IF EXISTS temp_mix_rescue_ranked;
    CREATE TEMP TABLE temp_mix_rescue_ranked AS
    SELECT c.id,
           s.deficit,
           row_number() OVER (
               PARTITION BY s.grid_id
               ORDER BY CASE
                   WHEN s.mixed_count = 0 THEN 0
                   ELSE (SELECT min(CASE WHEN ST_Touches(c.geom, m.geom) THEN 0
                                         ELSE ST_Distance(c.centroid, m.centroid) END)
                         FROM temp_buildings m
                         WHERE m.building_use = 'Mixed' AND ST_Contains(s.geom, m.centroid))
               END,
               md5(c.objectid)
           ) AS rescue_rank
    FROM temp_mix_shortfall s
    JOIN temp_buildings c
      ON c.building_use IN ('Residential', 'Commercial')
     AND c.floor_number >= 2
     AND ST_Contains(s.geom, c.centroid);

    UPDATE temp_buildings b
    SET building_use = 'Mixed'
    FROM temp_mix_rescue_ranked r
    WHERE b.id = r.id AND r.rescue_rank <= r.deficit;

    DROP TABLE IF EXISTS temp_mix_cell_state;
    DROP TABLE IF EXISTS temp_mix_shortfall;
    DROP TABLE IF EXISTS temp_mix_rescue_ranked;
END $$;

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
               WHEN b.building_use = 'Mixed' AND e.near_pedestrian_zone          THEN 'pedestrian'
               WHEN b.building_use = 'Mixed'                                     THEN 'standard'
               WHEN b.building_use = 'Residential'                               THEN 'full_residential'
               ELSE 'full_nonresidential'
           END AS rule
    FROM temp_buildings b
    JOIN temp_mix_evidence e ON e.id = b.id
),
commercial_floors AS (
    SELECT c.*,
           CASE c.rule
               WHEN 'pedestrian'         THEN {mu_commercial_floors_pedestrian}
               WHEN 'standard'           THEN {mu_commercial_floors_default}
               WHEN 'full_residential'   THEN 0
               ELSE c.floor_number
           END AS commercial_floors
    FROM classified c
)
SELECT id,
       rule,
       floor_area * floor_number AS gross_floor_area,
       CASE
           WHEN rule = 'full_residential'    THEN 1.0
           WHEN rule = 'full_nonresidential' THEN 0.0
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
DROP TABLE IF EXISTS temp_mix_validation;
DROP TABLE IF EXISTS temp_mix_decision;
DROP TABLE IF EXISTS temp_mix_promoted;
DROP TABLE IF EXISTS temp_mix_share;
DROP TABLE IF EXISTS temp_mix_evidence;
