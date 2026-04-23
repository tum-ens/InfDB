-- ============================================================
-- Assign buildings to a suitable way (writes buildings.assigned_way_id)
--
-- Notes:
-- - Builds a per-building candidate set scoped to `{ags}` and non-null centroids
-- - If `{use_address_information}` is TRUE:
--     - Prefer direct match via buildings.address_street_id = ways_tem.id
--     - Fallback to nearest suitable way within 2000 units
-- - If `{use_address_information}` is FALSE:
--     - Always use nearest suitable way within 2000 units
-- - Excludes ways where klasse = 'connection_line'
-- - Uses KNN ordering (centroid <-> geom) to pick the closest way (LIMIT 1)
-- ============================================================


-- 1) Compute best way per building, then update buildings table
WITH buildings_to_assign AS (
    SELECT
        b.id,               -- building primary key
        b.address_street_id, -- optional street reference for direct matching
        b.centroid          -- building centroid used for spatial matching
    FROM {output_schema}.buildings b
    WHERE b.centroid IS NOT NULL
        AND b.gemeindeschluessel = '{ags}' -- restrict to target AGS
),

best_way AS (
    SELECT
        b.id, -- building id
        COALESCE(direct_way.id, nearest_way.id) AS assigned_way_id -- direct match preferred, else nearest
    FROM buildings_to_assign b

    -- Direct match (only when flag is TRUE): address_street_id -> ways_tem.id
    LEFT JOIN ways_tem direct_way
        ON (
            {use_address_information}::boolean
            AND b.address_street_id IS NOT NULL
            AND direct_way.id = b.address_street_id::text   -- cast to text to match ways_tem.id type
            AND direct_way.klasse <> 'connection_line'      -- exclude connection lines
        )

    -- Nearest suitable way (fallback or always when flag is FALSE)
    LEFT JOIN LATERAL (
        SELECT w.id -- nearest way id
        FROM ways_tem w
        WHERE w.klasse <> 'connection_line'                 -- exclude connection lines
          AND ST_DWithin(b.centroid, w.geom, 2000)           -- search radius constraint
          AND ST_Distance(b.centroid, w.geom) > 0.1          -- avoid near-zero distances
        ORDER BY b.centroid <-> w.geom                       -- KNN: nearest geometry first
        LIMIT 1
    ) nearest_way
        ON (
            direct_way.id IS NULL                            -- only use fallback if no direct match
            OR NOT {use_address_information}::boolean         -- or always when address info disabled
        )

    -- Require that at least one candidate was found
    WHERE COALESCE(direct_way.id, nearest_way.id) IS NOT NULL
)

UPDATE {output_schema}.buildings b
SET assigned_way_id = bw.assigned_way_id -- write chosen way id
FROM best_way bw
WHERE b.id = bw.id; -- join back on building id