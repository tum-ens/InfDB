-- ============================================================
-- Building view (fortiss method) — output: {output_schema}.building_view
--
--   - One row per building WITHOUT building parts.
--   - One row per building PART (902) for multi-part buildings:
--       * geometry / part-specific attrs come from the part
--       * shared attrs (gemeindeschluessel, address) come from the parent
--   - geometry = lod2Solid faces (MultiPolygon), NOT a ground footprint.
--
-- No residential / scope filter here (kept identical to the fortiss query):
-- the table holds ALL buildings. Residential selection is applied downstream
-- (infdb-basedata-buildings / 02_fill_id_object_id_building_use.sql).
--
-- objectid is NOT unique for multi-part buildings (parent objectid is
-- repeated per part); the surrogate "id" column is the unique key.
-- ============================================================

DROP TABLE IF EXISTS {output_schema}.building_view;

CREATE TABLE {output_schema}.building_view AS
SELECT
    ROW_NUMBER() OVER () AS id,
    sub.*
FROM (
    -- ---- Buildings WITHOUT building parts -------------------------------
    SELECT
        f.id AS feature_id,
        f.objectid,
        gs.gemeindeschluessel,
        COALESCE(
            h.val_double,
            h.val_int::double precision,
            CASE
                WHEN h.val_string ~ '^[+-]?[0-9]+([.,][0-9]+)?$'
                THEN replace(h.val_string, ',', '.')::double precision
                ELSE NULL::double precision
            END
        ) AS height,
        addr.street,
        addr.house_number,
        addr.city,
        addr.state,
        addr.zip_code,
        fn.building_function_code,
        rt.rooftype_code,
        ga.grundrissaktualitaet,
        sa.storeysaboveground,
        g.geometry
    FROM feature f
        LEFT JOIN {helper_schema}.helper_lod2solid_geom     g   ON g.feature_id  = f.id
        LEFT JOIN {helper_schema}.helper_gemeindeschluessel gs  ON gs.feature_id = f.id
        LEFT JOIN {helper_schema}.helper_height             h   ON h.feature_id  = f.id
        LEFT JOIN {helper_schema}.helper_address            addr ON addr.feature_id = f.id
        LEFT JOIN {helper_schema}.helper_function           fn  ON fn.feature_id = f.id
        LEFT JOIN {helper_schema}.helper_rooftype           rt  ON rt.feature_id = f.id
        LEFT JOIN {helper_schema}.helper_grundrissaktualitaet ga ON ga.feature_id = f.id
        LEFT JOIN {helper_schema}.helper_storeys            sa  ON sa.feature_id = f.id
    WHERE f.objectclass_id = 901
      AND NOT EXISTS (
          SELECT 1 FROM {helper_schema}.helper_building_parts bp
          WHERE bp.parent_feature_id = f.id
      )

    UNION ALL

    -- ---- Building parts (geometry + part attrs from part) ---------------
    SELECT
        bp.part_feature_id AS feature_id,
        f.objectid,
        gs.gemeindeschluessel,
        COALESCE(
            h.val_double,
            h.val_int::double precision,
            CASE
                WHEN h.val_string ~ '^[+-]?[0-9]+([.,][0-9]+)?$'
                THEN replace(h.val_string, ',', '.')::double precision
                ELSE NULL::double precision
            END
        ) AS height,
        addr.street,
        addr.house_number,
        addr.city,
        addr.state,
        addr.zip_code,
        COALESCE(fn_parent.building_function_code, fn_part.building_function_code) AS building_function_code,
        rt.rooftype_code,
        ga.grundrissaktualitaet,
        sa.storeysaboveground,
        g.geometry
    FROM {helper_schema}.helper_building_parts bp
        JOIN feature f ON f.id = bp.parent_feature_id
        LEFT JOIN {helper_schema}.helper_lod2solid_geom     g   ON g.feature_id  = bp.part_feature_id
        LEFT JOIN {helper_schema}.helper_gemeindeschluessel gs  ON gs.feature_id = bp.parent_feature_id
        LEFT JOIN {helper_schema}.helper_height             h   ON h.feature_id  = bp.part_feature_id
        LEFT JOIN {helper_schema}.helper_address            addr ON addr.feature_id = bp.parent_feature_id
        LEFT JOIN {helper_schema}.helper_function           fn_parent ON fn_parent.feature_id = bp.parent_feature_id
        LEFT JOIN {helper_schema}.helper_function           fn_part   ON fn_part.feature_id   = bp.part_feature_id
        LEFT JOIN {helper_schema}.helper_rooftype           rt  ON rt.feature_id = bp.part_feature_id
        LEFT JOIN {helper_schema}.helper_grundrissaktualitaet ga ON ga.feature_id = bp.part_feature_id
        LEFT JOIN {helper_schema}.helper_storeys            sa  ON sa.feature_id = bp.part_feature_id
) sub;

CREATE INDEX ON {output_schema}.building_view (objectid);
CREATE INDEX ON {output_schema}.building_view (feature_id);
CREATE INDEX ON {output_schema}.building_view (gemeindeschluessel);
CREATE INDEX ON {output_schema}.building_view USING GIST (geometry);
