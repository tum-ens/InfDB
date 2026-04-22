-- ============================================================
-- Filter and delete selected ways, then reassign affected buildings
--
-- Notes:
-- - Identifies ways to delete based on:
--     1) Loops (start point equals end point)          → only if {apply_loop_filter} is TRUE
--     2) Isolated ways (no connections within snap tolerance) → only if apply_isolated_filter is TRUE
--     3) Short ways (below v_min_length threshold)     → only if {apply_length_filter} is TRUE
-- - Records deleted way ids, optional replacement ids, and deleted lengths in `filtered_ways`
-- - Deletes matching ways from `ways_tem`
-- - Transfers deleted length to `length_filter` of the replacement way (when available)
-- - Reassigns buildings.assigned_way_id using {output_schema}.update_assigned_way_id
-- ============================================================


-- Table to store deleted way IDs and their replacement ways
DROP TABLE IF EXISTS filtered_ways;
CREATE TEMP TABLE filtered_ways (
    old_way_id text NOT NULL,              -- deleted way id
    new_way_id text,                       -- replacement way id (NULL triggers nearest-way fallback downstream)
    old_length_geo double precision,       -- length of the deleted way for later aggregation
    filter_type text NOT NULL,             -- loop | short | isolated
    connection_count int                   -- number of connected ways detected
);
CREATE INDEX ON filtered_ways (old_way_id); -- lookup by deleted way id

DO $$
DECLARE
    v_min_length       double precision := {min_length_meter}::double precision; -- minimum length threshold (meters)
    v_snap_tol         double precision := 10.0;   -- snap/proximity tolerance for endpoint connections
    v_apply_loop       boolean          := {apply_loop_filter}::boolean;         -- enable loop filter
    v_apply_isolated   boolean          := {apply_isolated_filter}::boolean;     -- enable isolated filter
    v_apply_length     boolean          := {apply_length_filter}::boolean;       -- enable short-way filter
    r RECORD;              -- current way row under evaluation
    v_connected_way text;  -- chosen replacement way id (if applicable)
    v_filter_type text;    -- classification for why a way is filtered
    v_connection_count int; -- number of detected neighbour connections
    v_should_delete bool;  -- whether this way meets any active filter criterion
BEGIN
    -- Iterate ways_tem and classify ways for filtering
    FOR r IN
        SELECT
            w.id::text AS way_id,                        -- way id as text
            w.geom,                                      -- way geometry
            w.length_geo,                                -- stored geometric length
            ST_Length(w.geom) AS way_length,             -- computed length (same units as SRID)
            ST_StartPoint(w.geom) AS start_pt,           -- start endpoint
            ST_EndPoint(w.geom) AS end_pt,               -- end endpoint
            ST_Equals(ST_StartPoint(w.geom), ST_EndPoint(w.geom)) AS is_loop -- loop indicator
        FROM ways_tem w
        WHERE w.geom IS NOT NULL
          AND GeometryType(w.geom) = 'LINESTRING'         -- require LINESTRING
          AND NOT ST_IsEmpty(w.geom)
    LOOP
        -- Count neighbouring ways connected near either endpoint
        SELECT COUNT(*) INTO v_connection_count
        FROM ways_tem w2
        WHERE w2.id::text <> r.way_id                    -- exclude self
          AND w2.geom IS NOT NULL
          AND (ST_DWithin(w2.geom, r.start_pt, v_snap_tol)  -- near start endpoint
               OR ST_DWithin(w2.geom, r.end_pt, v_snap_tol)); -- near end endpoint

        -- Determine if this way should be deleted based on active filters
        v_should_delete := (
            (v_apply_loop     AND r.is_loop)                          -- loop filter
            OR
            (v_apply_isolated AND v_connection_count = 0)             -- isolated filter
            OR
            (v_apply_length   AND r.way_length < v_min_length         -- short filter
                              AND NOT r.is_loop                       --   (loops already handled above)
                              AND v_connection_count > 0)             --   (isolated already handled above)
        );

        IF v_should_delete THEN
            -- Assign filter type label — first matching active criterion wins
            v_filter_type := CASE
                WHEN v_apply_loop     AND r.is_loop                  THEN 'loop'
                WHEN v_apply_isolated AND v_connection_count = 0     THEN 'isolated'
                WHEN v_apply_length   AND r.way_length < v_min_length THEN 'short'
                ELSE 'unknown'
            END;

            -- Initialize replacement id (NULL means use nearest-way reassignment downstream)
            v_connected_way := NULL;

            -- For loops: attempt to pick a connected way near the loop endpoint
            IF v_apply_loop AND r.is_loop THEN
                SELECT w2.id::text INTO v_connected_way
                FROM ways_tem w2
                WHERE w2.id::text <> r.way_id
                  AND w2.geom IS NOT NULL
                  AND ST_DWithin(w2.geom, r.geom, v_snap_tol)   -- loop point proximity
                ORDER BY ST_Distance(w2.geom, r.geom) ASC        -- nearest connected geometry first
                LIMIT 1;
            END IF;

            -- Record deletion candidate and any selected replacement
            INSERT INTO filtered_ways (old_way_id, new_way_id, old_length_geo, filter_type, connection_count)
            VALUES (r.way_id, v_connected_way, r.length_geo, v_filter_type, v_connection_count);

        END IF;
    END LOOP;

    -- Delete all filtered ways from ways_tem
    DELETE FROM ways_tem
    WHERE id::text IN (SELECT old_way_id FROM filtered_ways);
END $$;

-- Transfer length_filter from deleted ways to their replacement ways
UPDATE ways_tem w
SET length_filter = COALESCE(w.length_filter, 0) + agg.total_transferred -- accumulate transferred length
FROM (
    SELECT
        new_way_id,                          -- replacement way id
        SUM(old_length_geo) AS total_transferred -- total deleted length assigned to this replacement
    FROM filtered_ways
    WHERE new_way_id IS NOT NULL             -- only where a replacement exists
    GROUP BY new_way_id
) agg
WHERE w.id::text = agg.new_way_id;           -- match replacement row

-- Reassign buildings affected by deleted ways using mapping table
SELECT {output_schema}.update_assigned_way_id(
    '{ags}',                    -- AGS scope for reassignment
    'filtered_ways'::regclass,  -- mapping table containing old/new ids
    'old_way_id',               -- column name for old ids
    'new_way_id'                -- column name for replacement ids (NULL triggers nearest fallback)
) AS buildings_updated;