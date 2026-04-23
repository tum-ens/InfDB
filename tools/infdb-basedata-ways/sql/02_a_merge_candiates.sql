-- ============================================================
-- Temporary merge-candidates table to find endpoint-based adjacency
--
-- Notes:
-- - Computes start/end points for each LINESTRING in `ways_tem`
-- - Builds `merge_candidates` with neighbour counts, neighbour id arrays, and nearest neighbour per endpoint
-- - Uses a configurable distance tolerance via `app.tol_m`
-- - Uses point-based GiST indexes for faster proximity joins
-- ============================================================

-- Configure endpoint proximity tolerance in meters (coordinate system dependent)
DO $$ BEGIN
    PERFORM set_config('app.tol_m', '0.20', false); -- distance threshold used by ST_DWithin
END $$;


-- Precompute endpoints once to reduce repeated ST_StartPoint/ST_EndPoint calls
DROP TABLE IF EXISTS way_endpoints;
CREATE TEMP TABLE way_endpoints AS
SELECT
    w.id::text            AS way_id,   -- segment id as text
    ST_StartPoint(w.geom) AS start_pt, -- start endpoint of the linestring
    ST_EndPoint(w.geom)   AS end_pt    -- end endpoint of the linestring
FROM ways_tem w
WHERE w.geom IS NOT NULL
  AND GeometryType(w.geom) = 'LINESTRING' -- require LINESTRING input geometry
  AND NOT ST_IsEmpty(w.geom);

-- Index endpoints for fast ST_DWithin lookups
CREATE INDEX way_endpoints_start_gix ON way_endpoints USING gist (start_pt); -- start point spatial index
CREATE INDEX way_endpoints_end_gix   ON way_endpoints USING gist (end_pt);   -- end point spatial index
CREATE INDEX way_endpoints_way_id_ix ON way_endpoints (way_id);              -- id lookup/join index


-- Create merge_candidates (schema matches downstream expectations)
DROP TABLE IF EXISTS merge_candidates;
CREATE TEMP TABLE merge_candidates (
    way_id text PRIMARY KEY, -- segment id

    start_pt              geometry(Point), -- start endpoint geometry
    start_cnt             integer          NOT NULL, -- neighbour count near start endpoint
    start_neighbor_ids    text[]           NOT NULL, -- neighbour ids near start endpoint
    start_nearest_id      text, -- nearest neighbour id near start endpoint
    start_nearest_dist_m  double precision, -- nearest neighbour distance near start endpoint

    end_pt                geometry(Point), -- end endpoint geometry
    end_cnt               integer          NOT NULL, -- neighbour count near end endpoint
    end_neighbor_ids      text[]           NOT NULL, -- neighbour ids near end endpoint
    end_nearest_id        text, -- nearest neighbour id near end endpoint
    end_nearest_dist_m    double precision, -- nearest neighbour distance near end endpoint

    tol_m                 double precision NOT NULL, -- tolerance used for this computation
    created_at            timestamptz DEFAULT now() -- creation timestamp
);

-- Index endpoints in merge_candidates for downstream spatial filtering
CREATE INDEX merge_candidates_start_pt_gix ON merge_candidates USING gist (start_pt); -- start point spatial index
CREATE INDEX merge_candidates_end_pt_gix   ON merge_candidates USING gist (end_pt);   -- end point spatial index


-- Fill merge_candidates using set-based endpoint joins
WITH
tol AS (
    SELECT current_setting('app.tol_m')::double precision AS m -- tolerance in meters
),

-- Aggregate neighbours for start endpoint
start_agg AS (
    SELECT
        b.way_id,

        COUNT(n.way_id)                                                         AS start_cnt, -- number of neighbours within tolerance
        COALESCE(
            array_agg(n.way_id ORDER BY n.way_id),
            ARRAY[]::text[]
        )                                                                        AS start_neighbor_ids, -- neighbour ids (sorted)

        (array_agg(n.way_id
                   ORDER BY ST_Distance(n.start_pt, b.start_pt)
                            + ST_Distance(n.end_pt,   b.start_pt)
        ))[1]                                                                    AS start_nearest_id, -- nearest neighbour id

        MIN(LEAST(
            ST_Distance(n.start_pt, b.start_pt),
            ST_Distance(n.end_pt,   b.start_pt)
        ))                                                                       AS start_nearest_dist_m -- nearest neighbour distance

    FROM way_endpoints b
    LEFT JOIN way_endpoints n
           ON n.way_id <> b.way_id -- exclude self
          AND (   ST_DWithin(n.start_pt, b.start_pt, (SELECT m FROM tol)) -- neighbour start near base start
               OR ST_DWithin(n.end_pt,   b.start_pt, (SELECT m FROM tol))) -- neighbour end near base start
    GROUP BY b.way_id
),

-- Aggregate neighbours for end endpoint
end_agg AS (
    SELECT
        b.way_id,

        COUNT(n.way_id)                                                         AS end_cnt, -- number of neighbours within tolerance
        COALESCE(
            array_agg(n.way_id ORDER BY n.way_id),
            ARRAY[]::text[]
        )                                                                        AS end_neighbor_ids, -- neighbour ids (sorted)

        (array_agg(n.way_id
                   ORDER BY ST_Distance(n.start_pt, b.end_pt)
                            + ST_Distance(n.end_pt,   b.end_pt)
        ))[1]                                                                    AS end_nearest_id, -- nearest neighbour id

        MIN(LEAST(
            ST_Distance(n.start_pt, b.end_pt),
            ST_Distance(n.end_pt,   b.end_pt)
        ))                                                                       AS end_nearest_dist_m -- nearest neighbour distance

    FROM way_endpoints b
    LEFT JOIN way_endpoints n
           ON n.way_id <> b.way_id -- exclude self
          AND (   ST_DWithin(n.start_pt, b.end_pt, (SELECT m FROM tol)) -- neighbour start near base end
               OR ST_DWithin(n.end_pt,   b.end_pt, (SELECT m FROM tol))) -- neighbour end near base end
    GROUP BY b.way_id
)

INSERT INTO merge_candidates (
    way_id,
    start_pt, start_cnt, start_neighbor_ids, start_nearest_id, start_nearest_dist_m,
    end_pt,   end_cnt,   end_neighbor_ids,   end_nearest_id,   end_nearest_dist_m,
    tol_m
)
SELECT
    b.way_id,

    b.start_pt,
    COALESCE(sa.start_cnt, 0)::integer, -- default to 0 neighbours
    COALESCE(sa.start_neighbor_ids, ARRAY[]::text[]), -- default to empty array
    sa.start_nearest_id,
    sa.start_nearest_dist_m,

    b.end_pt,
    COALESCE(ea.end_cnt, 0)::integer, -- default to 0 neighbours
    COALESCE(ea.end_neighbor_ids, ARRAY[]::text[]), -- default to empty array
    ea.end_nearest_id,
    ea.end_nearest_dist_m,

    (SELECT m FROM tol) -- store tolerance used for the computation
FROM way_endpoints b
LEFT JOIN start_agg sa ON sa.way_id = b.way_id -- attach start-endpoint aggregates
LEFT JOIN end_agg   ea ON ea.way_id = b.way_id; -- attach end-endpoint aggregates


-- Cleanup helper table
DROP TABLE IF EXISTS way_endpoints;