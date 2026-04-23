-- ============================================================
-- Creates shared functions and tables for parallel AGS processing
-- 
-- Purpose:
--   - Creates shared functions used across all workers
--   - Creates global output tables used by all AGS workers
--   - Uses an advisory lock to prevent race conditions during first-time setup
--
-- Safety:
--   - Uses pg_try_advisory_lock() for atomic coordination
--   - First worker to acquire lock creates resources (idempotently)
--   - Other workers wait briefly then proceed
--   - All workers verify critical resources exist before continuing
-- ============================================================

DO $$
DECLARE
    -- Unique lock key for initialization coordination
    -- All workers compete for this same lock
    lock_key bigint := 999999999;
    
    -- Flag indicating if this worker acquired the lock
    got_lock boolean;
BEGIN
    -- ================================================================
    -- STEP 1: Try to acquire initialization lock (non-blocking)
    -- ================================================================
    -- pg_try_advisory_lock returns immediately:
    --   TRUE  = lock acquired, this worker will create resources
    --   FALSE = lock held by another worker, wait for them to finish
    got_lock := pg_try_advisory_lock(lock_key);
    
    IF got_lock THEN
        -- ============================================================
        -- PATH A: This worker won the lock race
        -- ============================================================
        
        -- Idempotency check: only create shared resources if missing
        IF NOT EXISTS (
            SELECT 1 FROM pg_tables 
            WHERE schemaname = '{output_schema}' 
              AND tablename = 'ways_per_junction'
        ) THEN
            -- ========================================================
            -- Resources don't exist - create them now
            -- ========================================================
            
            -- --------------------------------------------------------
            -- Function 1: update_assigned_way_id
            -- --------------------------------------------------------
            -- Updates buildings.assigned_way_id using a mapping table
            -- Falls back to nearest suitable way when no mapped replacement exists
            CREATE OR REPLACE FUNCTION {output_schema}.update_assigned_way_id(
                p_ags text,                       -- AGS scope to restrict affected buildings
                p_mapping_table regclass,         -- mapping table (old->new way ids) passed as relation
                p_old_way_col text,               -- column name in mapping table for old way id
                p_new_way_col text DEFAULT 'new_way_id' -- column name in mapping table for new way id
            )
            RETURNS bigint
            LANGUAGE plpgsql
            AS $func$
            DECLARE
                v_updated bigint := 0; -- number of buildings updated in this call
                v_sql text;            -- dynamic SQL to support flexible mapping table/column inputs
            BEGIN
                v_sql := format(
                    'WITH buildings_to_reassign AS (
                        SELECT
                            b.id,
                            b.centroid,
                            b.assigned_way_id,
                            m.%I AS old_way_id,
                            m.%I AS new_way_id
                        FROM {output_schema}.buildings AS b
                        JOIN %s AS m ON b.assigned_way_id = m.%I
                        WHERE b.centroid IS NOT NULL
                          AND b.gemeindeschluessel = %L
                    ),
                    best_replacement AS (
                        SELECT
                            btr.id,
                            COALESCE(
                                btr.new_way_id,
                                (SELECT w.id::text
                                 FROM ways_tem w
                                 WHERE w.klasse <> ''110''
                                   AND ST_DWithin(btr.centroid, w.geom, 2000)
                                   AND ST_Distance(btr.centroid, w.geom) > 0.1
                                   AND w.id::text <> btr.old_way_id
                                 ORDER BY btr.centroid <-> w.geom
                                 LIMIT 1
                                )
                            ) AS assigned_way_id
                        FROM buildings_to_reassign btr
                    )
                    UPDATE {output_schema}.buildings AS b
                    SET assigned_way_id = br.assigned_way_id
                    FROM best_replacement br
                    WHERE b.id = br.id
                      AND br.assigned_way_id IS NOT NULL',
                    p_old_way_col, -- formatted identifier for old-way column
                    p_new_way_col, -- formatted identifier for new-way column
                    p_mapping_table, -- mapping table relation substituted into query
                    p_old_way_col, -- join column identifier (old way id)
                    p_ags -- literal AGS value for scoping
                );

                EXECUTE v_sql; -- execute reassignment update for this AGS
                GET DIAGNOSTICS v_updated = ROW_COUNT; -- capture affected row count
                
                RETURN v_updated; -- return updated building count
            END;
            $func$;
            
            -- --------------------------------------------------------
            -- Function 2: insert_way_segment
            -- --------------------------------------------------------
            -- Inserts a new segment into ways_tem, ways_tem_connection, or connection_lines_tem
            CREATE OR REPLACE FUNCTION {output_schema}.insert_way_segment(
                p_ags text,       -- AGS tag for inserted segment
                p_klasse text,    -- class determining target table (connection_line vs segmented_way vs road)
                p_geom geometry,  -- segment geometry in expected SRID/type
                p_connected_way_id text DEFAULT NULL
            ) RETURNS void
            LANGUAGE plpgsql
            AS $func$
            DECLARE
                v_new text; -- generated id for the new segment
            BEGIN
                IF p_geom IS NULL THEN -- ignore NULL geometry inserts
                    RETURN;
                END IF;

                IF ST_IsEmpty(p_geom) THEN -- ignore empty geometry inserts
                    RETURN;
                END IF;

                IF GeometryType(p_geom) <> 'LINESTRING' THEN -- ignore non-linestring inserts
                    RETURN;
                END IF;

                IF ST_Length(p_geom) = 0 THEN -- ignore zero-length degenerate linestrings
                    RETURN;
                END IF;

                v_new := md5(random()::text || clock_timestamp()::text); -- generate unique-ish text id

                IF p_klasse = 'connection_line' THEN -- route connection lines to their temp table
                    INSERT INTO connection_lines_tem (ags, id, connected_way_id, klasse, objektart, geom, postcode)
                    VALUES (p_ags, v_new, p_connected_way_id, p_klasse, NULL, p_geom, NULL);
                ELSIF p_klasse = 'segmented_way' THEN -- route segmented ways to ways_tem_connection
                    INSERT INTO ways_tem_connection (ags, id, klasse, objektart, geom, postcode)
                    VALUES (p_ags, v_new, p_klasse, NULL, p_geom, NULL);
                ELSE -- route all other classes to ways_tem
                    INSERT INTO ways_tem (ags, id, klasse, objektart, geom, postcode)
                    VALUES (p_ags, v_new, p_klasse, NULL, p_geom, NULL);
                END IF;
            END;
            $func$;
            
            -- --------------------------------------------------------
            -- Function 3: split_way_at_connection_points
            -- --------------------------------------------------------
            -- Splits a line into multiple LINESTRING parts at ordered points
            CREATE OR REPLACE FUNCTION {output_schema}.split_way_at_connection_points(
                line geometry,         -- input line geometry to split
                points geometry[]      -- array of split points along the line
            )
            RETURNS TABLE(part geometry) 
            LANGUAGE plpgsql
            AS $func$
            DECLARE
                i INTEGER;                 -- loop index over point array
                start_fraction FLOAT := 0; -- start fraction for current substring
                end_fraction FLOAT;        -- end fraction for current substring
            BEGIN
                -- Iterate through all split points
                FOR i IN 1 .. array_length(points, 1)
                LOOP
                    -- Calculate fractional position of current point along line
                    end_fraction := ST_LineLocatePoint(line, points[i]);
                    
                    -- Extract segment if valid (end > start)
                    IF end_fraction > start_fraction THEN
                        RETURN QUERY
                        SELECT ST_LineSubstring(line, start_fraction, end_fraction);
                    END IF;
                    
                    -- Update start position for next iteration
                    start_fraction := end_fraction;
                END LOOP;

                -- Handle final segment (last point to line end)
                IF start_fraction < 1 THEN
                    RETURN QUERY
                    SELECT ST_LineSubstring(line, start_fraction, 1);
                END IF;
            END;
            $func$;
            
            -- --------------------------------------------------------
            -- Function 4: generate_building_way_connection_candidates
            -- --------------------------------------------------------
            -- Builds a temp table of connection lines from buildings to assigned ways
            CREATE OR REPLACE FUNCTION {output_schema}.generate_building_way_connection_candidates()
            RETURNS void
            LANGUAGE plpgsql
            AS $func$
            BEGIN
                DROP TABLE IF EXISTS temp_building_connection_candidates; -- reset temp table per session

                CREATE TEMP TABLE temp_building_connection_candidates AS
                WITH b AS (
                    SELECT
                        b.id               AS building_id,      -- building primary key
                        b.centroid         AS center,           -- building centroid point geometry
                        b.assigned_way_id                    -- assigned way reference (text)
                    FROM {output_schema}.buildings b
                    WHERE b.centroid IS NOT NULL              -- require centroid for spatial ops
                      AND b.assigned_way_id IS NOT NULL       -- require assigned way id
                ),
                matched AS (
                    SELECT
                        b.building_id,
                        b.center,
                        w.id               AS old_way_id,       -- resolved way id in ways_tem
                        w.geom             AS old_geom,         -- resolved way geometry
                        w.ags              AS old_way_ags       -- AGS tag of resolved way
                    FROM b
                    JOIN ways_tem w
                      ON w.id = b.assigned_way_id::text         -- match on text id
                    WHERE w.geom IS NOT NULL                    -- require geometry
                      AND w.klasse <> 'connection_line'         -- exclude connection lines from target ways
                ),
                computed AS (
                    SELECT
                        m.building_id,
                        m.center,
                        m.old_way_id,
                        m.old_geom,
                        m.old_way_ags,
                        ST_ShortestLine(m.center, m.old_geom) AS new_geom, -- connection line geometry
                        ST_ClosestPoint(m.old_geom, m.center) AS connection_point -- projected point on way
                    FROM matched m
                )
                SELECT DISTINCT ON (building_id)
                    building_id,
                    center,
                    new_geom,
                    old_way_id,
                    old_geom,
                    old_way_ags,
                    connection_point
                FROM computed;

                CREATE INDEX temp_candidates_old_way_idx
                    ON temp_building_connection_candidates (old_way_id); -- lookup by way id

                CREATE INDEX temp_candidates_connection_gix
                    ON temp_building_connection_candidates
                    USING GIST (connection_point); -- spatial ops on connection points
            END;
            $func$;

            -- --------------------------------------------------------
            -- Function 5: update_assigned_way_id_after_merge
            -- --------------------------------------------------------
            -- Updates buildings.assigned_way_id using a mapping table for merged ways


            CREATE OR REPLACE FUNCTION {output_schema}.update_assigned_way_id_after_merge(
                p_ags text
            )
            RETURNS bigint
            LANGUAGE plpgsql
            AS $func$
            DECLARE
                v_updated bigint := 0;
            BEGIN
                WITH buildings_to_reassign AS (
                    SELECT
                        b.id,
                        b.centroid,
                        b.assigned_way_id,
                        m.new_way_id
                    FROM {output_schema}.buildings AS b
                    JOIN merged_ways_mapping m ON b.assigned_way_id = m.old_way_id
                    WHERE b.gemeindeschluessel = p_ags
                )
                UPDATE {output_schema}.buildings AS b
                SET assigned_way_id = btr.new_way_id
                FROM buildings_to_reassign btr
                WHERE b.id = btr.id
                AND btr.new_way_id IS NOT NULL;

                GET DIAGNOSTICS v_updated = ROW_COUNT;
                RETURN v_updated;
            END;
            $func$;
            
            -- --------------------------------------------------------
            -- Table: ways_per_junction (global output table)
            -- --------------------------------------------------------
            -- Create empty table with the same column layout as ways_tem
            DROP TABLE IF EXISTS {output_schema}.ways_per_junction; -- ensure clean table for this session
            CREATE TABLE {output_schema}.ways_per_junction AS
            SELECT
                ags,                   -- municipality/region id (AGS) as text
                id,                    -- segment id as text
                klasse,                -- feature class
                objektart,             -- feature type
                geom,                  -- segment geometry
                postcode,              -- postcode enrichment (filled later)
                length_geo,            -- stored geometric length
                length_filter,         -- bookkeeping accumulator
                length_connection_line -- bookkeeping accumulator for connection lines
            FROM ways_tem
            WHERE false;  -- Creates structure only, no data

            ALTER TABLE {output_schema}.ways_per_junction
            ADD COLUMN changelog_id BIGINT REFERENCES public.changelog(id) ON DELETE SET NULL;

            -- Set required key columns to NOT NULL
            ALTER TABLE {output_schema}.ways_per_junction
                ALTER COLUMN ags SET NOT NULL,
                ALTER COLUMN id  SET NOT NULL;

            -- Indexes for scoped reads and spatial predicates
            CREATE INDEX ways_per_junction_ags_idx
                ON {output_schema}.ways_per_junction (ags);

            CREATE INDEX ways_per_junction_geom_gix
                ON {output_schema}.ways_per_junction USING GIST (geom);

            -- Prevent duplicates per AGS+id
            CREATE UNIQUE INDEX ways_per_junction_ags_id_ux
                ON {output_schema}.ways_per_junction (ags, id);

            -- --------------------------------------------------------
            -- Table: ways_per_connection (global output table)
            -- --------------------------------------------------------
            -- Create empty table with the same column layout as ways_tem
            DROP TABLE IF EXISTS {output_schema}.ways_per_connection; -- ensure clean table for this session
            CREATE TABLE {output_schema}.ways_per_connection AS
            SELECT
                ags,                   -- municipality/region id (AGS) as text
                id,                    -- segment id as text
                klasse,                -- feature class
                objektart,             -- feature type
                geom,                  -- segment geometry
                postcode,              -- postcode enrichment (filled later)
                length_geo,            -- stored geometric length
                length_filter,         -- bookkeeping accumulator
                length_connection_line -- bookkeeping accumulator for connection lines
            FROM ways_tem
            WHERE false;  -- Creates structure only, no data

            ALTER TABLE {output_schema}.ways_per_connection
            ADD COLUMN changelog_id BIGINT REFERENCES public.changelog(id) ON DELETE SET NULL;

            -- Set required key columns to NOT NULL
            ALTER TABLE {output_schema}.ways_per_connection
                ALTER COLUMN ags SET NOT NULL,
                ALTER COLUMN id  SET NOT NULL;

            -- Indexes for scoped reads and spatial predicates
            CREATE INDEX ways_per_connection_ags_idx
                ON {output_schema}.ways_per_connection (ags);

            CREATE INDEX ways_per_connection_geom_gix
                ON {output_schema}.ways_per_connection USING GIST (geom);

            -- Prevent duplicates per AGS+id
            CREATE UNIQUE INDEX ways_per_connection_ags_id_ux
                ON {output_schema}.ways_per_connection (ags, id);
            
            -- --------------------------------------------------------
            -- Table: connection_lines (global output table)
            -- --------------------------------------------------------
            -- Create empty table with the same column layout as connection_lines_tem
            DROP TABLE IF EXISTS {output_schema}.connection_lines; -- ensure clean table for this session
            CREATE TABLE {output_schema}.connection_lines AS
            SELECT
                ags,                   -- municipality/region id (AGS) as text
                id,                    -- segment id as text
                connected_way_id,      -- id of the way in ways_tem this connection belongs to
                klasse,                -- feature class
                objektart,             -- feature type
                geom,                  -- segment geometry
                postcode,              -- postcode enrichment (filled later)
                length_geo,            -- stored geometric length
                length_filter,         -- bookkeeping accumulator
                length_connection_line -- bookkeeping accumulator for connection lines
            FROM connection_lines_tem
            WHERE false;  -- creates structure only, no data

            ALTER TABLE {output_schema}.connection_lines
            ADD COLUMN changelog_id BIGINT REFERENCES public.changelog(id) ON DELETE SET NULL;

            -- Set required key columns to NOT NULL
            ALTER TABLE {output_schema}.connection_lines
                ALTER COLUMN ags SET NOT NULL,
                ALTER COLUMN id  SET NOT NULL;

            -- Indexes for scoped reads and spatial predicates
            CREATE INDEX connection_lines_ags_idx
                ON {output_schema}.connection_lines (ags);

            CREATE INDEX connection_lines_geom_gix
                ON {output_schema}.connection_lines USING GIST (geom);

            CREATE INDEX connection_lines_connected_way_id_idx
                ON {output_schema}.connection_lines (connected_way_id);

            -- Prevent duplicates per AGS+id
            CREATE UNIQUE INDEX connection_lines_ags_id_ux
                ON {output_schema}.connection_lines (ags, id);
            
            -- --------------------------------------------------------
            -- Table: nodes_per_connection (global output table)
            -- Nodes are street connection points
            -- Columns:
            --   ags      text                          NOT NULL
            --   id       text                          NOT NULL
            --   geom     geometry(Point)               NOT NULL
            --   way_ids  text[]                        NOT NULL
            -- --------------------------------------------------------

            DROP TABLE IF EXISTS {output_schema}.nodes_per_connection; -- recreate nodes_per_connection table idempotently

            -- Create empty table structure (no rows)
            CREATE TABLE {output_schema}.nodes_per_connection AS
            SELECT
                CAST(NULL AS text)            AS ags,     -- municipality/region id (AGS) as text
                CAST(NULL AS text)            AS id,      -- node id as text
                CAST(NULL AS geometry(Point)) AS geom,    -- node point geometry
                CAST(NULL AS text[])          AS way_ids  -- associated way ids
            WHERE false;

            ALTER TABLE {output_schema}.nodes_per_connection
            ADD COLUMN changelog_id BIGINT REFERENCES public.changelog(id) ON DELETE SET NULL;

            -- Constraints
            ALTER TABLE {output_schema}.nodes_per_connection
                ALTER COLUMN ags     SET NOT NULL,
                ALTER COLUMN id      SET NOT NULL,
                ALTER COLUMN geom    SET NOT NULL,
                ALTER COLUMN way_ids SET NOT NULL;

            -- Default empty array for way_ids
            ALTER TABLE {output_schema}.nodes_per_connection
                ALTER COLUMN way_ids SET DEFAULT ARRAY[]::text[];

            -- Indexes
            CREATE INDEX nodes_per_connection_ags_idx
                ON {output_schema}.nodes_per_connection (ags); -- AGS scoped filtering

            CREATE INDEX nodes_per_connection_geom_gix
                ON {output_schema}.nodes_per_connection USING GIST (geom); -- spatial predicates / nearest-neighbor

            CREATE INDEX nodes_per_connection_way_ids_gin
                ON {output_schema}.nodes_per_connection USING GIN (way_ids); -- array membership queries

            
            -- Prevent duplicates per AGS+id
            CREATE UNIQUE INDEX nodes_per_connection_ags_id_ux
                ON {output_schema}.nodes_per_connection (ags, id);
            
            -- --------------------------------------------------------
            -- Table: nodes_per_junction (global output table)
            -- Nodes are street connection points
            -- Columns:
            --   ags      text                          NOT NULL
            --   id       text                          NOT NULL
            --   geom     geometry(Point)               NOT NULL
            --   way_ids  text[]                        NOT NULL
            -- --------------------------------------------------------

            DROP TABLE IF EXISTS {output_schema}.nodes_per_junction; -- recreate nodes_per_junction table idempotently

            -- Create empty table structure (no rows)
            CREATE TABLE {output_schema}.nodes_per_junction AS
            SELECT
                CAST(NULL AS text)            AS ags,     -- municipality/region id (AGS) as text
                CAST(NULL AS text)            AS id,      -- node id as text
                CAST(NULL AS geometry(Point)) AS geom,    -- node point geometry
                CAST(NULL AS text[])          AS way_ids  -- associated way ids
            WHERE false;

            ALTER TABLE {output_schema}.nodes_per_junction
            ADD COLUMN changelog_id BIGINT REFERENCES public.changelog(id) ON DELETE SET NULL;

            -- Constraints
            ALTER TABLE {output_schema}.nodes_per_junction
                ALTER COLUMN ags     SET NOT NULL,
                ALTER COLUMN id      SET NOT NULL,
                ALTER COLUMN geom    SET NOT NULL,
                ALTER COLUMN way_ids SET NOT NULL;

            -- Default empty array for way_ids
            ALTER TABLE {output_schema}.nodes_per_junction
                ALTER COLUMN way_ids SET DEFAULT ARRAY[]::text[];

            -- Indexes
            CREATE INDEX nodes_per_junction_ags_idx
                ON {output_schema}.nodes_per_junction (ags); -- AGS scoped filtering

            CREATE INDEX nodes_per_junction_geom_gix
                ON {output_schema}.nodes_per_junction USING GIST (geom); -- spatial predicates / nearest-neighbor

            CREATE INDEX nodes_per_junction_way_ids_gin
                ON {output_schema}.nodes_per_junction USING GIN (way_ids); -- array membership queries

            -- Prevent duplicates per AGS+id
            CREATE UNIQUE INDEX nodes_per_junction_ags_id_ux
                ON {output_schema}.nodes_per_junction (ags, id);




            
            -- --------------------------------------------------------
            -- Column: buildings.assigned_way_id
            -- --------------------------------------------------------
            -- Ensure the column exists (idempotent)
            ALTER TABLE {output_schema}.buildings
                ADD COLUMN IF NOT EXISTS assigned_way_id text; -- assigned way id as text
            
        ELSE
            -- ========================================================
            -- Resources already exist - skip creation
            -- ========================================================
        END IF;
        
        -- Release the lock so other workers can proceed
        PERFORM pg_advisory_unlock(lock_key); -- unlock initialization key
        
    ELSE
        -- ============================================================
        -- PATH B: Another worker is creating resources
        -- ============================================================
        
        -- Wait for the other worker to finish
        PERFORM pg_sleep(3); -- allow initializer to finish creating shared resources
        
    END IF;
    
    -- ================================================================
    -- STEP 2: Verify resources exist (safety check for all workers)
    -- ================================================================
    -- Ensure initialization succeeded before any worker proceeds
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE schemaname = '{output_schema}' 
          AND tablename = 'ways_per_junction'
    ) THEN
        RAISE EXCEPTION '[Init] FATAL ERROR: ways_per_junction table does not exist after initialization. Check logs for errors.';
    END IF;
    
    -- Verify critical functions exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc 
        WHERE proname = 'split_way_at_connection_points' 
          AND pronamespace = '{output_schema}'::regnamespace
    ) THEN
        RAISE EXCEPTION '[Init] FATAL ERROR: split_way_at_connection_points function does not exist after initialization. Check logs for errors.';
    END IF;
    
    -- ================================================================
    -- STEP 3: All clear - ready to proceed
    -- ================================================================
    
END $$;