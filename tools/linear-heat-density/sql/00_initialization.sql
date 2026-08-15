-- ============================================================
-- Creates shared schema, table and indexes for parallel AGS processing
--
-- Purpose:
--   - Creates the global output table used by all AGS workers
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
    lock_key bigint := 99999996;

    -- Flag indicating if this worker acquired the lock
    got_lock boolean;
BEGIN
    -- ================================================================
    -- STEP 1: Try to acquire initialization lock (non-blocking)
    -- ================================================================
    got_lock := pg_try_advisory_lock(lock_key);

    IF got_lock THEN
        -- ============================================================
        -- PATH A: This worker won the lock race
        -- ============================================================

        -- Idempotency check: only create shared resources if missing
        IF NOT EXISTS (
            SELECT 1 FROM pg_tables
            WHERE schemaname = '{output_schema}'
              AND tablename = '{output_table}'
        ) THEN
            CREATE SCHEMA IF NOT EXISTS {output_schema};

            -- Linear heat density per street segment
            CREATE TABLE IF NOT EXISTS {output_schema}.{output_table} (
                street_id TEXT PRIMARY KEY,
                geom GEOMETRY,
                total_heat_demand NUMERIC,
                street_length NUMERIC,
                linear_heat_density NUMERIC,
                gemeindeschluessel TEXT,
                changelog_id      BIGINT REFERENCES public.changelog(id) ON DELETE SET NULL
            );

            -- Spatial predicates and AGS scoped reads
            CREATE INDEX IF NOT EXISTS idx_{output_table}_geom
                ON {output_schema}.{output_table} USING GIST (geom);

            CREATE INDEX IF NOT EXISTS idx_{output_table}_gemeindeschluessel
                ON {output_schema}.{output_table} (gemeindeschluessel);
        END IF;

        -- Release the lock so other workers can proceed
        PERFORM pg_advisory_unlock(lock_key);

    ELSE
        -- ============================================================
        -- PATH B: Another worker is creating resources
        -- ============================================================
        PERFORM pg_sleep(3); -- allow initializer to finish creating shared resources

    END IF;

    -- ================================================================
    -- STEP 2: Verify resources exist (safety check for all workers)
    -- ================================================================
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables
        WHERE schemaname = '{output_schema}'
          AND tablename = '{output_table}'
    ) THEN
        RAISE EXCEPTION '[Init] FATAL ERROR: {output_schema}.{output_table} does not exist after initialization. Check logs for errors.';
    END IF;

END $$;
