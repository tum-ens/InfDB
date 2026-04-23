DO $$
DECLARE
    v_changelog_id BIGINT;
BEGIN
-- create a new changelog id and store it in a variable for later reference in the insert statements
SELECT public.fn_begin_changelog('{tool_name}', 'no comment', session_user::TEXT, '{ags}', '{process_id}') INTO v_changelog_id;

-- ============================================================
-- Persist per-AGS results from temp tables into global output tables
--
-- Notes:
-- - Replaces existing rows for the target `{ags}` to keep outputs idempotent
-- - Copies final road segments from `ways_tem` into `{output_schema}.ways_per_junction`
-- - Copies final connection line segments from `connection_lines_tem` into `{output_schema}.connection_lines`
-- - Copies final road segments from `ways_tem_connection` into `{output_schema}.ways_per_connection`
-- - Assumes temp tables contain only valid rows for the current pipeline stage
-- ============================================================


-- Replace existing segmented ways for this AGS
DELETE FROM {output_schema}.ways_per_junction
WHERE ags = '{ags}'; -- restrict delete to current AGS scope

INSERT INTO {output_schema}.ways_per_junction (ags, id, klasse, objektart, geom, postcode, length_geo, length_filter, length_connection_line, changelog_id)
SELECT
  ags,                      -- municipality/region id (AGS) as text
  id,                       -- segment id as text
  klasse,                   -- feature class
  objektart,                -- feature type
  geom,                     -- segment geometry
  postcode,                 -- postcode enrichment
  length_geo,               -- stored geometric length
  length_filter,            -- bookkeeping accumulator
  length_connection_line,   -- bookkeeping accumulator for connection lines
  v_changelog_id            -- changelog reference
FROM ways_tem
WHERE ags = '{ags}';         -- copy only rows for the current AGS


-- Replace existing segmented ways for this AGS
DELETE FROM {output_schema}.ways_per_connection
WHERE ags = '{ags}'; -- restrict delete to current AGS scope

INSERT INTO {output_schema}.ways_per_connection (ags, id, klasse, objektart, geom, postcode, length_geo, length_filter, length_connection_line, changelog_id)
SELECT
  ags,                      -- municipality/region id (AGS) as text
  id,                       -- segment id as text
  klasse,                   -- feature class
  objektart,                -- feature type
  geom,                     -- segment geometry
  postcode,                 -- postcode enrichment
  length_geo,               -- stored geometric length
  length_filter,            -- bookkeeping accumulator
  length_connection_line,   -- bookkeeping accumulator for connection lines
  v_changelog_id            -- changelog reference
FROM ways_tem_connection
WHERE ags = '{ags}';         -- copy only rows for the current AGS


-- Replace existing connection lines for this AGS
DELETE FROM {output_schema}.connection_lines
WHERE ags = '{ags}'; -- restrict delete to current AGS scope

INSERT INTO {output_schema}.connection_lines (ags, id, connected_way_id, klasse, objektart, geom, postcode, length_geo, length_filter, length_connection_line, changelog_id)
SELECT
  ags,                      -- municipality/region id (AGS) as text
  id,                       -- segment id as text
  connected_way_id,        -- id of the way in ways_tem this connection belongs to
  klasse,                   -- feature class
  objektart,                -- feature type
  geom,                     -- segment geometry
  postcode,                 -- postcode enrichment
  length_geo,               -- stored geometric length
  length_filter,            -- bookkeeping accumulator
  length_connection_line,   -- bookkeeping accumulator for connection lines
  v_changelog_id            -- changelog reference
FROM connection_lines_tem
WHERE ags = '{ags}';          -- copy only rows for the current AGS

END;
$$;