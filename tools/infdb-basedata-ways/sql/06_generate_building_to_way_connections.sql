-- ============================================================
-- End-to-end pipeline: generate and insert building connection lines, split affected ways
--
-- Notes:
-- - Phase 1: Generates building-to-way connection candidates in a temp table
-- - Phase 2: Inserts connection lines into the connection_lines temp table via insert_way_segment()
--     - If connection point is near the start/end of the way (< 0.15), connect directly to that endpoint
--       and remove the candidate (no splitting required)
--     - Otherwise, insert the precomputed shortest line (splitting may be applied later)
-- - Phase 2b: Aggregates connection line lengths per affected way and updates ways_tem.length_connection_line
-- - Phase 2c: Copies ways_tem to ways_tem_connection for segmentation
-- - Phase 3: Groups remaining connection points per affected way into grouped_splits (ordered along the line)
-- - Phase 4: Deletes original ways from ways_tem_connection and reinserts split segments using split_way_at_connection_points()
-- ============================================================

DO $$
DECLARE
    s RECORD; -- current grouped_splits row (old_way_id, old_geom, old_way_ags, connection_points)
    part geometry; -- one returned segment geometry from split_way_at_connection_points
BEGIN
    -- Phase 1: generate building-to-way connection candidates
    PERFORM {output_schema}.generate_building_way_connection_candidates();


    -- Phase 2: insert connection lines (near-start cases)
    PERFORM {output_schema}.insert_way_segment(
        c.old_way_ags,                                    -- AGS tag for inserted segment
        'connection_line',                                -- class routes insert into connection_lines_tem
        ST_MakeLine(c.center, ST_StartPoint(c.old_geom)),   -- connect building center to way start endpoint
        c.old_way_id -- id of the connected way 
    )
    FROM temp_building_connection_candidates c
    WHERE ST_Distance(ST_StartPoint(c.old_geom), c.connection_point) < 0.15; -- near-start threshold

    DELETE FROM temp_building_connection_candidates
    WHERE ST_Distance(ST_StartPoint(old_geom), connection_point) < 0.15; -- remove handled candidates


    -- Phase 2: insert connection lines (near-end cases)
    PERFORM {output_schema}.insert_way_segment(
        c.old_way_ags,                                  -- AGS tag for inserted segment
        'connection_line',                              -- class routes insert into connection_lines_tem
        ST_MakeLine(c.center, ST_EndPoint(c.old_geom)),   -- connect building center to way end endpoint
        c.old_way_id -- id of the connected way 
    )
    FROM temp_building_connection_candidates c
    WHERE ST_Distance(ST_EndPoint(c.old_geom), c.connection_point) < 0.15; -- near-end threshold

    DELETE FROM temp_building_connection_candidates
    WHERE ST_Distance(ST_EndPoint(old_geom), connection_point) < 0.15; -- remove handled candidates


    -- Phase 2: insert remaining connection lines (mid-point cases)
    PERFORM {output_schema}.insert_way_segment(
        c.old_way_ags,          -- AGS tag for inserted segment
        'connection_line',      -- class routes insert into connection_lines_tem
        c.new_geom,              -- precomputed shortest connection line
        c.old_way_id -- id of the connected way 
    )
    FROM temp_building_connection_candidates c;


    -- Phase 2b: accumulate total connection line length per old_way_id into ways_tem.length_connection_line
    UPDATE ways_tem w
    SET length_connection_line = COALESCE(length_connection_line, 0) + agg.total_length -- accumulate length
    FROM (
        SELECT
            old_way_id,                      -- affected way id
            SUM(ST_Length(new_geom)) AS total_length -- summed connection line length for that way
        FROM temp_building_connection_candidates
        GROUP BY old_way_id
    ) agg
    WHERE w.id = agg.old_way_id; -- match affected way row


    -- Phase 2c: copy ways_tem to ways_tem_connection for segmentation
    DROP TABLE IF EXISTS ways_tem_connection;
    CREATE TEMP TABLE ways_tem_connection AS
    SELECT * FROM ways_tem;


    -- Phase 3: group ordered split points per affected way
    DROP TABLE IF EXISTS grouped_splits;
    CREATE TEMP TABLE grouped_splits AS
    SELECT
        old_way_id, -- way id to be split
        old_geom,   -- original way geometry to split
        old_way_ags, -- AGS tag of the way
        ARRAY_AGG(connection_point ORDER BY ST_LineLocatePoint(old_geom, connection_point)) AS connection_points -- ordered points
    FROM temp_building_connection_candidates
    GROUP BY old_way_id, old_geom, old_way_ags;

    -- Phase 4: delete original ways from ways_tem_connection prior to reinserting split segments
    DELETE FROM ways_tem_connection
    WHERE id IN (SELECT old_way_id FROM grouped_splits); -- bulk delete originals from connection table

    -- Reinsert split segments for each affected way
    FOR s IN SELECT * FROM grouped_splits LOOP
        FOR part IN
            SELECT * FROM {output_schema}.split_way_at_connection_points(s.old_geom, s.connection_points) -- split into segments
        LOOP
            PERFORM {output_schema}.insert_way_segment(
                s.old_way_ags,     -- AGS tag for inserted segment
                'segmented_way',   -- class label for inserted segment (routes to ways_tem_connection)
                part               -- segment geometry
            );
        END LOOP;
    END LOOP;

END;
$$;