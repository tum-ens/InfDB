DO $$
DECLARE
    v_changelog_id BIGINT;
BEGIN
-- create a new changelog id and store it in a variable for later reference in the insert statements
SELECT public.fn_begin_changelog('{tool_name}', 'no comment', session_user::TEXT, '{ags}', '{process_id}') INTO v_changelog_id;

-- ============================================================
-- Build nodes at connection points between ways in ways_tem and ways_tem_connection
--
-- Notes:
-- - A node is created wherever 2+ way endpoints meet within a tolerance
-- - Deletes existing nodes for the target `{ags}` and reinserts computed nodes
-- - Computes endpoints (start/end) for LINESTRING ways in ways_tem
-- - Clusters endpoints using ST_ClusterDBSCAN with a fixed tolerance
-- - Aggregates clusters into node geometries and associated way id arrays
-- - Inserts results into {output_schema}.nodes_per_junction (from ways_tem)
-- - Inserts results into {output_schema}.nodes_per_connection (from ways_tem_connection)
-- ============================================================

-- Clean existing nodes for this AGS scope
DELETE FROM {output_schema}.nodes_per_junction
WHERE ags = '{ags}'; -- restrict delete to current AGS

-- Clean existing nodes_per_connection for this AGS scope
DELETE FROM {output_schema}.nodes_per_connection
WHERE ags = '{ags}'; -- restrict delete to current AGS

-- Insert nodes from ways_tem
WITH params AS (
    SELECT 0.20::double precision AS tol_m -- clustering tolerance (units depend on SRID)
),

-- Precompute endpoints (start and end points for each way)
endpoints AS (
    SELECT
        w.id::text            AS way_id, -- way id as text
        w.ags                 AS ags,    -- municipality/region id (AGS) as text
        ST_StartPoint(w.geom) AS pt      -- start endpoint point
    FROM ways_tem w
    WHERE w.geom IS NOT NULL
      AND GeometryType(w.geom) = 'LINESTRING' -- require LINESTRING
      AND NOT ST_IsEmpty(w.geom)

    UNION ALL

    SELECT
        w.id::text           AS way_id, -- way id as text
        w.ags                AS ags,    -- municipality/region id (AGS) as text
        ST_EndPoint(w.geom)  AS pt      -- end endpoint point
    FROM ways_tem w
    WHERE w.geom IS NOT NULL
      AND GeometryType(w.geom) = 'LINESTRING' -- require LINESTRING
      AND NOT ST_IsEmpty(w.geom)
),

-- Cluster endpoints that lie within tol_m of each other
clustered AS (
    SELECT
        way_id, -- way id
        ags,    -- AGS tag
        pt,     -- endpoint geometry
        ST_ClusterDBSCAN(pt, (SELECT tol_m FROM params), 1)
            OVER () AS cluster_id -- cluster id across all endpoints
    FROM endpoints
),

-- Aggregate clusters into node points and associated way ids
cluster_stats AS (
    SELECT
        cluster_id,                                  -- cluster identifier
        array_agg(DISTINCT way_id ORDER BY way_id) AS way_ids, -- distinct way ids in this cluster
        MIN(ags)                                    AS ags,    -- AGS tag for the node
        ST_Centroid(ST_Collect(pt))                 AS node_pt -- representative node point
    FROM clustered
    WHERE cluster_id IS NOT NULL                    -- ignore unclustered points
    GROUP BY cluster_id
    HAVING COUNT(DISTINCT way_id) >= 1              -- cluster size threshold (distinct ways)
)

-- Insert aggregated clusters as nodes_per_junction
INSERT INTO {output_schema}.nodes_per_junction (ags, id, geom, way_ids, changelog_id)
SELECT
    ags,                                     -- municipality/region id (AGS) as text
    md5(node_pt::text || cluster_id::text) AS id, -- deterministic-ish node id from geometry+cluster
    node_pt                                AS geom, -- node point geometry
    way_ids                                AS way_ids, -- associated way ids
    v_changelog_id                         AS changelog_id -- changelog reference
FROM cluster_stats;


-- Insert nodes_per_connection from ways_tem_connection
WITH params AS (
    SELECT 0.20::double precision AS tol_m -- clustering tolerance (units depend on SRID)
),

-- Precompute endpoints (start and end points for each way)
endpoints AS (
    SELECT
        w.id::text            AS way_id, -- way id as text
        w.ags                 AS ags,    -- municipality/region id (AGS) as text
        ST_StartPoint(w.geom) AS pt      -- start endpoint point
    FROM ways_tem_connection w
    WHERE w.geom IS NOT NULL
      AND GeometryType(w.geom) = 'LINESTRING' -- require LINESTRING
      AND NOT ST_IsEmpty(w.geom)

    UNION ALL

    SELECT
        w.id::text           AS way_id, -- way id as text
        w.ags                AS ags,    -- municipality/region id (AGS) as text
        ST_EndPoint(w.geom)  AS pt      -- end endpoint point
    FROM ways_tem_connection w
    WHERE w.geom IS NOT NULL
      AND GeometryType(w.geom) = 'LINESTRING' -- require LINESTRING
      AND NOT ST_IsEmpty(w.geom)
),

-- Cluster endpoints that lie within tol_m of each other
clustered AS (
    SELECT
        way_id, -- way id
        ags,    -- AGS tag
        pt,     -- endpoint geometry
        ST_ClusterDBSCAN(pt, (SELECT tol_m FROM params), 1)
            OVER () AS cluster_id -- cluster id across all endpoints
    FROM endpoints
),

-- Aggregate clusters into node points and associated way ids
cluster_stats AS (
    SELECT
        cluster_id,                                  -- cluster identifier
        array_agg(DISTINCT way_id ORDER BY way_id) AS way_ids, -- distinct way ids in this cluster
        MIN(ags)                                    AS ags,    -- AGS tag for the node
        ST_Centroid(ST_Collect(pt))                 AS node_pt -- representative node point
    FROM clustered
    WHERE cluster_id IS NOT NULL                    -- ignore unclustered points
    GROUP BY cluster_id
    HAVING COUNT(DISTINCT way_id) >= 1              -- cluster size threshold (distinct ways)
)

-- Insert aggregated clusters as nodes_per_connection
INSERT INTO {output_schema}.nodes_per_connection (ags, id, geom, way_ids, changelog_id)
SELECT
    ags,                                     -- municipality/region id (AGS) as text
    md5(node_pt::text || cluster_id::text) AS id, -- deterministic-ish node id from geometry+cluster
    node_pt                                AS geom, -- node point geometry
    way_ids                                AS way_ids, -- associated way ids
    v_changelog_id                         AS changelog_id -- changelog reference
FROM cluster_stats;

END;
$$;