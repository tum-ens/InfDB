-- ============================================================
-- Creates shared schema, tables and views for parallel AGS processing
--
-- Purpose:
--   - Creates the global output tables used by all AGS workers
--   - Uses an advisory lock to prevent race conditions during first-time setup
--
-- Safety:
--   - Uses pg_try_advisory_lock() for atomic coordination
--   - First worker to acquire lock creates resources (idempotently)
--   - Other workers wait briefly then proceed
--   - All workers verify critical resources exist before continuing
--
-- Only the tables required by the configured method are created, so an unused
-- method's output table never exists as an empty table.
-- ============================================================

DO $$
DECLARE
    -- Unique lock key for initialization coordination
    -- All workers compete for this same lock
    lock_key bigint := 99999997;

    -- Flag indicating if this worker acquired the lock
    got_lock boolean;

    -- Method specific output table, used as the idempotency sentinel
    sentinel text := CASE
        WHEN '{method}' = '1R0C_internal' THEN 'annual_heating_demand'
        ELSE 'entise_summary'
    END;
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
              AND tablename = sentinel
        ) THEN
            CREATE SCHEMA IF NOT EXISTS {output_schema};

            -- Simulated refurbishment state per building
            CREATE TABLE IF NOT EXISTS {output_schema}.buildings_refurbished_status
            (
                building_objectid TEXT PRIMARY KEY,
                floor_area DOUBLE PRECISION,
                floor_number BIGINT,
                building_type TEXT,
                construction_year BIGINT,
                wall_area DOUBLE PRECISION,
                roof_area DOUBLE PRECISION,
                window_area DOUBLE PRECISION,
                outer_wall BIGINT,
                rooftop BIGINT,
                "window" BIGINT,
                changelog_id      BIGINT REFERENCES public.changelog(id) ON DELETE SET NULL
            );

            -- Thermal resistance and capacitance per building
            CREATE TABLE IF NOT EXISTS {output_schema}.buildings_rc
            (
                building_objectid TEXT PRIMARY KEY,
                resistance DOUBLE PRECISION,
                capacitance DOUBLE PRECISION,
                changelog_id      BIGINT REFERENCES public.changelog(id) ON DELETE SET NULL
            );

            IF '{method}' = '1R0C_internal' THEN
                -- Annual heating demand
                CREATE TABLE IF NOT EXISTS {output_schema}.annual_heating_demand
                (
                    building_objectid text PRIMARY KEY,
                    "heating:demand[kWh]" double precision,
                    pmax double precision,
                    changelog_id      BIGINT REFERENCES public.changelog(id) ON DELETE SET NULL
                );

                -- Heat demand joined with building attributes for inspection
                CREATE OR REPLACE VIEW {output_schema}.debug_demand AS
                SELECT
                    ahd."heating:demand[kWh]",
                    ((ahd."heating:demand[kWh]") / (brs.floor_area * brs.floor_number)) AS "heating:demand_per_area[kWh/m²]",
                    brc.resistance,
                    brc.capacitance,
                    brs.*,
                    bbl.id,
                    bbl.feature_id,
                    bbl.height,
                    bbl.building_use,
                    bbl.building_use_id,
                    bbl.occupants,
                    bbl.households,
                    bbl.postcode,
                    bbl.address_street_id,
                    bbl.street,
                    bbl.house_number,
                    bbl.gemeindeschluessel,
                    bbl.centroid,
                    bbl.geom
                FROM {output_schema}.buildings_refurbished_status brs
                JOIN {output_schema}.annual_heating_demand ahd ON brs.building_objectid = ahd.building_objectid
                JOIN {output_schema}.buildings_rc brc ON brs.building_objectid = brc.building_objectid
                JOIN basedata.buildings bbl ON brs.building_objectid = bbl.objectid;
            ELSE
                -- Time series summary
                CREATE TABLE IF NOT EXISTS {output_schema}.entise_summary
                (
                    building_objectid TEXT PRIMARY KEY,
                    "heating:demand[Wh]" DOUBLE PRECISION,
                    "heating:load_max[W]" DOUBLE PRECISION,
                    "cooling:demand[Wh]" DOUBLE PRECISION,
                    "cooling:load_max[W]" DOUBLE PRECISION
                );
            END IF;
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
          AND tablename = sentinel
    ) THEN
        RAISE EXCEPTION '[Init] FATAL ERROR: {output_schema}.% does not exist after initialization. Check logs for errors.', sentinel;
    END IF;

END $$;
