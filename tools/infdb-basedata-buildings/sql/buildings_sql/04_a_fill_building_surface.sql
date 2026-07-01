-- Fill temp_building_surface from {input_schema}.building_surface (fortiss).
--
-- The fortiss building_surface leaves the `area` column NULL, so we derive it
-- here, per AGS:
--   * directly from LOD2 (the `Flaeche` attribute on the surface feature in
--     citydb) where available (e.g. Bavaria), else
--   * computed set-based (no SFCGAL): per-surface outward normal via Newell's
--     method, then surface_area_corrected_geom() rotates the face flat and
--     takes ST_Area (holes/tilt handled correctly).
--
-- Column mapping vs the fortiss building_surface: classname -> surface_type,
-- geom -> geometry. surface_gmlid is unique per surface, so it keys the normals
-- back onto the scoped surfaces.
INSERT INTO temp_building_surface
WITH scoped AS (
    -- Surfaces in this AGS, plus the direct LOD2 Flaeche where present.
    SELECT
        bs.building_objectid,
        bs.objectclass_id,
        bs.surface_type,
        bs.gemeindeschluessel,
        bs.surface_gmlid,
        bs.geometry,
        fl.flaeche
    FROM {input_schema}.building_surface bs
    LEFT JOIN citydb.feature sf
           ON sf.objectid = bs.surface_gmlid
    LEFT JOIN LATERAL (
        SELECT MAX(p.val_string)::double precision AS flaeche
        FROM citydb.property p
        WHERE p.feature_id = sf.id
          AND p.name = 'Flaeche'
    ) fl ON TRUE
    WHERE bs.gemeindeschluessel = '{ags}'
),
-- Vertices of the surfaces that still need a computed area (no direct Flaeche),
-- paired with their successor around the ring (ring-then-vertex order so holed
-- polygons are traversed correctly).
edges AS (
    SELECT
        s.surface_gmlid,
        dp.geom AS pg,
        LEAD(dp.geom) OVER (
            PARTITION BY s.surface_gmlid
            ORDER BY dp.path[1], dp.path[2]
        ) AS npt
    FROM scoped s
    CROSS JOIN LATERAL ST_DumpPoints(s.geometry) AS dp
    WHERE s.flaeche IS NULL
),
-- Newell's method: the surface outward normal (direction only).
normals AS (
    SELECT
        surface_gmlid,
        SUM((ST_Y(pg) - ST_Y(npt)) * (ST_Z(pg) + ST_Z(npt))) AS nx,
        SUM((ST_Z(pg) - ST_Z(npt)) * (ST_X(pg) + ST_X(npt))) AS ny,
        SUM((ST_X(pg) - ST_X(npt)) * (ST_Y(pg) + ST_Y(npt))) AS nz
    FROM edges
    WHERE npt IS NOT NULL
    GROUP BY surface_gmlid
)
SELECT
    s.building_objectid,
    s.objectclass_id,
    s.surface_type,
    COALESCE(
        s.flaeche,
        {output_schema}.surface_area_corrected_geom(s.geometry, n.nx, n.ny, n.nz)
    ) AS area,
    s.gemeindeschluessel,
    (s.flaeche IS NULL) AS is_synthetic
FROM scoped s
LEFT JOIN normals n ON n.surface_gmlid = s.surface_gmlid;
