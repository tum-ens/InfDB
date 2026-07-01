-- ============================================================
-- Building surface (fortiss method) — output: {output_schema}.building_surface
--
-- Links each thematic surface (709 Wall / 710 Ground / 712 Roof) to its
-- building via the direct property.boundary FK -- no children-hash, no JSON
-- explosion, no self-join.
--   - Branch A: buildings WITHOUT parts -> surfaces of the 901 building.
--   - Branch B: buildings WITH parts    -> surfaces of each 902 part,
--                                          attributed to the parent's objectid.
--
-- Keeps only real envelope faces (709/710/712), excluding virtual
-- ClosureSurfaces (15).
--
-- gemeindeschluessel is attached in the SAME CREATE via a join to the small
-- helper_bld_gemeindeschluessel (objectid -> gemeindeschluessel). This is a
-- single pass -- no post-hoc full-table UPDATE -- which matters at whole-state
-- scale. The pure fortiss two-branch query is kept verbatim as the sub inner
-- SELECT.
--
-- Depends on helper_building_parts and helper_bld_gemeindeschluessel
-- (from building_helpers.sql).
-- ============================================================

DROP TABLE IF EXISTS {output_schema}.building_surface;

CREATE TABLE {output_schema}.building_surface AS
SELECT
    sub.*,
    g.gemeindeschluessel
FROM (

    -- ---- BRANCH A: buildings without building parts ----------------------
    SELECT
        gd.geometry,
        sf.objectid            AS surface_gmlid,
        sf.objectclass_id,
        CASE sf.objectclass_id
            WHEN 709 THEN 'WallSurface'
            WHEN 710 THEN 'GroundSurface'
            WHEN 712 THEN 'RoofSurface'
            ELSE 'Other'
        END                    AS surface_type,
        bf.objectid            AS building_objectid,
        NULL::double precision AS area,
        NULL::double precision AS z_min,
        NULL::double precision AS z_min_asl,
        NULL::double precision AS z_max,
        NULL::double precision AS z_max_asl
    FROM property sh
    JOIN feature bf ON bf.id = sh.feature_id AND bf.objectclass_id = 901
    JOIN feature sf ON sf.id = sh.val_feature_id
                   AND sf.objectclass_id = ANY (ARRAY[709, 710, 712])
    JOIN geometry_data gd ON gd.feature_id = sf.id
    WHERE sh.name = 'boundary'
      AND NOT EXISTS (
          SELECT 1 FROM {helper_schema}.helper_building_parts bp
          WHERE bp.parent_feature_id = bf.id
      )

    UNION ALL

    -- ---- BRANCH B: building parts ----------------------------------------
    SELECT
        gd.geometry,
        sf.objectid,
        sf.objectclass_id,
        CASE sf.objectclass_id
            WHEN 709 THEN 'WallSurface'
            WHEN 710 THEN 'GroundSurface'
            WHEN 712 THEN 'RoofSurface'
            ELSE 'Other'
        END,
        bf.objectid,
        NULL::double precision,
        NULL::double precision,
        NULL::double precision,
        NULL::double precision,
        NULL::double precision
    FROM {helper_schema}.helper_building_parts hbp
    JOIN feature bf   ON bf.id   = hbp.parent_feature_id
    JOIN feature part ON part.id = hbp.part_feature_id
    JOIN property sh  ON sh.feature_id = part.id AND sh.name = 'boundary'
    JOIN feature sf   ON sf.id = sh.val_feature_id
                   AND sf.objectclass_id = ANY (ARRAY[709, 710, 712])
    JOIN geometry_data gd ON gd.feature_id = sf.id

) sub
LEFT JOIN {helper_schema}.helper_bld_gemeindeschluessel g
       ON g.building_objectid = sub.building_objectid;

-- Indexes (only those the pipeline needs, plus GIST for QGIS/spatial use):
--   gemeindeschluessel -> per-AGS filter in infdb-basedata-buildings
--   building_objectid  -> group/join per building
--   objectclass_id     -> 710 (ground) filter
--   geometry (GIST)    -> spatial / QGIS
CREATE INDEX ON {output_schema}.building_surface (gemeindeschluessel);
CREATE INDEX ON {output_schema}.building_surface (building_objectid);
CREATE INDEX ON {output_schema}.building_surface (objectclass_id);
CREATE INDEX ON {output_schema}.building_surface USING GIST (geometry);

ANALYZE {output_schema}.building_surface;
