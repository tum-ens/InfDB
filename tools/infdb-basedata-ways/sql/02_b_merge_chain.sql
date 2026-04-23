-- ============================================================
-- Builds connected components ("chains") based on merge_candidates
--
-- Output tables (temporary):
--   - chain_edges: normalized undirected edges between way ids
--   - chain_membership: node -> component_id mapping for each connected component
--   - chain_candidates: one row per component with ordered way id array
--
-- Notes:
-- - Uses only endpoints with exactly one neighbour (cnt = 1) to form edges
-- - Normalizes edges via LEAST/GREATEST to represent an undirected graph
-- - Computes connected components using a union-find implementation in PL/pgSQL
-- ============================================================


-- 1) Build undirected edges from merge_candidates (only cnt=1 endpoints)
DROP TABLE IF EXISTS chain_edges;
CREATE TEMP TABLE chain_edges AS
WITH raw_edges AS (
    SELECT
        mc.way_id           AS a, -- base way id
        mc.start_nearest_id AS b  -- nearest neighbour at start endpoint
    FROM merge_candidates mc
    WHERE mc.start_cnt = 1
      AND mc.start_nearest_id IS NOT NULL

    UNION ALL

    SELECT
        mc.way_id         AS a, -- base way id
        mc.end_nearest_id AS b  -- nearest neighbour at end endpoint
    FROM merge_candidates mc
    WHERE mc.end_cnt = 1
      AND mc.end_nearest_id IS NOT NULL
),
norm AS (
    SELECT
        LEAST(a, b)    AS u, -- canonical smaller endpoint id
        GREATEST(a, b) AS v  -- canonical larger endpoint id
    FROM raw_edges
    WHERE a <> b            -- exclude self-loops
)
SELECT DISTINCT u, v        -- de-duplicate edges
FROM norm;

CREATE INDEX IF NOT EXISTS chain_edges_u_idx ON chain_edges (u); -- lookup edges by u
CREATE INDEX IF NOT EXISTS chain_edges_v_idx ON chain_edges (v); -- lookup edges by v


-- 2) Connected components via union-find over chain_edges
DROP TABLE IF EXISTS chain_membership;

CREATE OR REPLACE FUNCTION _build_chain_membership()
RETURNS void LANGUAGE plpgsql AS $$
DECLARE
    r       RECORD;   -- current edge row (u, v)
    root_a  text;     -- root representative for u
    root_b  text;     -- root representative for v
    tmp     text;     -- temporary parent pointer during traversal
    v_rows  integer;  -- number of rows updated in a flatten pass
BEGIN
    -- Initialize union-find parent pointers: each node is its own parent
    CREATE TEMP TABLE _uf_parent (
        node   text PRIMARY KEY, -- node id (way id)
        parent text NOT NULL     -- parent pointer (root if parent=node)
    ) ON COMMIT DROP;

    INSERT INTO _uf_parent (node, parent)
    SELECT DISTINCT node, node -- initial parent is self
    FROM (
        SELECT u AS node FROM chain_edges
        UNION
        SELECT v         FROM chain_edges
    ) x;

    -- Union pass: iterate edges and merge components
    FOR r IN SELECT u, v FROM chain_edges LOOP

        -- Find root of u by following parent pointers
        root_a := r.u;
        LOOP
            SELECT parent INTO tmp FROM _uf_parent WHERE node = root_a;
            EXIT WHEN tmp = root_a;
            root_a := tmp;
        END LOOP;

        -- Find root of v by following parent pointers
        root_b := r.v;
        LOOP
            SELECT parent INTO tmp FROM _uf_parent WHERE node = root_b;
            EXIT WHEN tmp = root_b;
            root_b := tmp;
        END LOOP;

        -- Union: deterministic choice of root based on text ordering
        IF root_a <> root_b THEN
            IF root_a < root_b THEN
                UPDATE _uf_parent SET parent = root_a WHERE node = root_b; -- attach b-root under a-root
            ELSE
                UPDATE _uf_parent SET parent = root_b WHERE node = root_a; -- attach a-root under b-root
            END IF;
        END IF;

    END LOOP;

    -- Flatten parent pointers until all nodes point directly to their root
    LOOP
        UPDATE _uf_parent p
        SET    parent = g.parent
        FROM   _uf_parent g
        WHERE  p.parent = g.node
          AND  g.parent <> g.node; -- only collapse non-root links

        GET DIAGNOSTICS v_rows = ROW_COUNT; -- detect convergence
        EXIT WHEN v_rows = 0;
    END LOOP;

    -- Materialize final membership mapping: node -> component_id
    CREATE TEMP TABLE chain_membership AS
    SELECT
        node,               -- way id
        parent AS component_id -- connected component representative
    FROM _uf_parent;

    -- _uf_parent dropped automatically at end of transaction (ON COMMIT DROP)
END $$;

SELECT _build_chain_membership();
DROP FUNCTION IF EXISTS _build_chain_membership();

CREATE INDEX IF NOT EXISTS chain_membership_component_idx ON chain_membership (component_id); -- group by component
CREATE INDEX IF NOT EXISTS chain_membership_node_idx      ON chain_membership (node);        -- lookup by node


-- 3) Aggregate components into chain_candidates (one row per component)
DROP TABLE IF EXISTS chain_candidates;
CREATE TEMP TABLE chain_candidates AS
SELECT
    component_id                  AS chain_id,   -- component representative id
    array_agg(node ORDER BY node) AS way_ids,    -- ordered member way ids
    count(*)                      AS way_count   -- number of ways in the chain
FROM chain_membership
GROUP BY component_id
HAVING count(*) >= 2; -- keep only multi-way components

CREATE INDEX IF NOT EXISTS chain_candidates_way_count_idx ON chain_candidates (way_count); -- filter/sort by size