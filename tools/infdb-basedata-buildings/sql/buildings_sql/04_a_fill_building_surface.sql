-- Fill temp_building_surface from {input_schema}.building_surface (fortiss).
--
-- The fortiss building_surface leaves the `area` column NULL, so we derive it
-- here, per AGS:
--   * directly from LOD2 (the `Flaeche` attribute on the surface feature in
--     citydb) where available (e.g. Bavaria), else
--   * computed set-based: a surface geometry can hold several polygon
--     faces with different orientations, so the area is computed per face -- each
--     face gets its own Newell normal, surface_area_corrected_geom() rotates that
--     face flat and takes ST_Area (holes/tilt handled correctly), and the face
--     areas are summed back to the surface.
--
-- Column mapping vs the fortiss building_surface: classname -> surface_type,
-- geom -> geometry. surface_gmlid is unique per surface, so it keys the per-face
-- areas back onto the scoped surfaces.
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
-- Explode each surface that still needs a computed area (no direct Flaeche) into
-- its polygon faces, so faces with different orientations are measured
-- independently. face_idx is the polygon index within the surface geometry.
faces AS (
    SELECT
        s.surface_gmlid,
        (fd.path)[1] AS face_idx,
        fd.geom      AS face
    FROM scoped s
    CROSS JOIN LATERAL ST_Dump(s.geometry) AS fd
    WHERE s.flaeche IS NULL
),
-- Vertices of each face, paired with the successor in vertex order. Ordering by
-- the full dp.path (ring, vertex) keeps the vertices sequential, which the Newell
-- normal below relies on.
edges AS (
    SELECT
        f.surface_gmlid,
        f.face_idx,
        f.face,
        dp.geom AS pg,
        LEAD(dp.geom) OVER (
            PARTITION BY f.surface_gmlid, f.face_idx
            ORDER BY dp.path
        ) AS npt
    FROM faces f
    CROSS JOIN LATERAL ST_DumpPoints(f.face) AS dp
),
-- Newell's method: each face's outward normal (direction only).
face_normals AS (
    SELECT
        surface_gmlid,
        face_idx,
        SUM((ST_Y(pg) - ST_Y(npt)) * (ST_Z(pg) + ST_Z(npt))) AS nx,
        SUM((ST_Z(pg) - ST_Z(npt)) * (ST_X(pg) + ST_X(npt))) AS ny,
        SUM((ST_X(pg) - ST_X(npt)) * (ST_Y(pg) + ST_Y(npt))) AS nz
    FROM edges
    WHERE npt IS NOT NULL
    GROUP BY surface_gmlid, face_idx
),
-- Sum the per-face areas back to a single area per surface.
face_areas AS (
    SELECT
        fn.surface_gmlid,
        SUM({output_schema}.surface_area_corrected_geom(f.face, fn.nx, fn.ny, fn.nz)) AS area
    FROM face_normals fn
    JOIN faces f
      ON f.surface_gmlid = fn.surface_gmlid
     AND f.face_idx = fn.face_idx
    GROUP BY fn.surface_gmlid
)
SELECT
    s.building_objectid,
    s.objectclass_id,
    s.surface_type,
    COALESCE(s.flaeche, fa.area) AS area,
    s.gemeindeschluessel,
    (s.flaeche IS NULL) AS is_synthetic
FROM scoped s
LEFT JOIN face_areas fa ON fa.surface_gmlid = s.surface_gmlid;
