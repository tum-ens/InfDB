-- Buildings improvements for Lizmap integration
--
-- This script adds:
--   1. data integrity constraints
--   2. a history table for logging
--   3. a trigger + trigger function for the logging
--   4. building revert function
--
-- Safe to execute multiple times.


-- Data integrity constraints
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'occupants_reasonable'
    ) THEN
        ALTER TABLE {output_schema}.buildings
            ADD CONSTRAINT occupants_reasonable
            CHECK (occupants >= 0 AND occupants <= 500);
    END IF;
END $$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'floors_not_negative'
    ) THEN
        ALTER TABLE {output_schema}.buildings
            ADD CONSTRAINT floors_not_negative
            CHECK (floor_number > 0);
    END IF;
END $$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'height_not_negative'
    ) THEN
        ALTER TABLE {output_schema}.buildings
            ADD CONSTRAINT height_not_negative
            CHECK (height > 0);
    END IF;
END $$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'households_reasonable'
    ) THEN
        ALTER TABLE {output_schema}.buildings
            ADD CONSTRAINT households_reasonable
            CHECK (households >= 0 AND households <= occupants);
    END IF;
END $$;



-- History table
-- PostgreSQL assigns a newly created table to the connection role configured
-- by SERVICES_POSTGRES_USER; no separate ownership change is needed.

CREATE TABLE IF NOT EXISTS {output_schema}.buildings_history
(
    history_id serial PRIMARY KEY,
    building_id integer NOT NULL,
    operation text NOT NULL,
    changed_at timestamp DEFAULT now(),
    old_data jsonb,
    new_data jsonb
);

-- Logging trigger function
CREATE OR REPLACE FUNCTION {output_schema}.log_buildings_changes()
RETURNS trigger AS
$$
BEGIN

    IF TG_OP = 'UPDATE' THEN

        INSERT INTO {output_schema}.buildings_history
        (
            building_id,
            operation,
            old_data,
            new_data
        )
        VALUES
        (
            NEW.id,
            'UPDATE',
            to_jsonb(OLD),
            to_jsonb(NEW)
        );

        RETURN NEW;

    ELSIF TG_OP = 'INSERT' THEN

        INSERT INTO {output_schema}.buildings_history
        (
            building_id,
            operation,
            new_data
        )
        VALUES
        (
            NEW.id,
            'INSERT',
            to_jsonb(NEW)
        );

        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN

        INSERT INTO {output_schema}.buildings_history
        (
            building_id,
            operation,
            old_data
        )
        VALUES
        (
            OLD.id,
            'DELETE',
            to_jsonb(OLD)
        );

        RETURN OLD;

    END IF;

END;
$$
LANGUAGE plpgsql;


-- Logging trigger
DROP TRIGGER IF EXISTS trg_buildings_audit
ON {output_schema}.buildings;

CREATE TRIGGER trg_buildings_audit
AFTER INSERT OR UPDATE OR DELETE
ON {output_schema}.buildings
FOR EACH ROW
EXECUTE FUNCTION {output_schema}.log_buildings_changes();



-- Revert function for the history table
-- Usage:
-- SELECT {output_schema}.revert_building(history_id);
CREATE OR REPLACE FUNCTION {output_schema}.revert_building(p_history_id integer)
RETURNS void
AS
$$
DECLARE
    h RECORD;
    v_current jsonb;
BEGIN

    -- Load history record
    SELECT *
    INTO h
    FROM {output_schema}.buildings_history
    WHERE history_id = p_history_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'History row % not found', p_history_id;
    END IF;


    -- Capture current state
    SELECT to_jsonb(b)
    INTO v_current
    FROM {output_schema}.buildings b
    WHERE b.id = h.building_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Building % not found', h.building_id;
    END IF;


    -- Restore previous values
    UPDATE {output_schema}.buildings b
    SET

        geom =
            CASE
                WHEN h.old_data ? 'geom'
                THEN ST_SetSRID(
                    ST_GeomFromGeoJSON(h.old_data->'geom'),
                    25832
                )
                ELSE b.geom
            END,

        centroid =
            CASE
                WHEN h.old_data ? 'centroid'
                THEN ST_SetSRID(
                    ST_GeomFromGeoJSON(h.old_data->'centroid'),
                    25832
                )
                ELSE b.centroid
            END,

        height = COALESCE((h.old_data->>'height')::numeric, b.height),
        street = COALESCE(h.old_data->>'street', b.street),
        objectid = COALESCE(h.old_data->>'objectid', b.objectid),
        postcode = COALESCE((h.old_data->>'postcode')::integer, b.postcode),
        occupants = COALESCE((h.old_data->>'occupants')::integer, b.occupants),
        feature_id = COALESCE((h.old_data->>'feature_id')::bigint, b.feature_id),
        floor_area = COALESCE((h.old_data->>'floor_area')::numeric, b.floor_area),
        households = COALESCE((h.old_data->>'households')::integer, b.households),
        building_use = COALESCE(h.old_data->>'building_use', b.building_use),
        changelog_id = COALESCE((h.old_data->>'changelog_id')::integer, b.changelog_id),
        floor_number = COALESCE((h.old_data->>'floor_number')::integer, b.floor_number),
        house_number = COALESCE(h.old_data->>'house_number', b.house_number),
        building_type = COALESCE(h.old_data->>'building_type', b.building_type),
        assigned_way_id = COALESCE(h.old_data->>'assigned_way_id', b.assigned_way_id),
        building_use_id = COALESCE(h.old_data->>'building_use_id', b.building_use_id),
        address_street_id = COALESCE((h.old_data->>'address_street_id')::integer, b.address_street_id),
        construction_year = COALESCE(h.old_data->>'construction_year', b.construction_year),
        gemeindeschluessel = COALESCE(h.old_data->>'gemeindeschluessel', b.gemeindeschluessel)

    WHERE b.id = h.building_id;


    -- Log the revert
    INSERT INTO {output_schema}.buildings_history
    (
        building_id,
        operation,
        changed_at,
        old_data,
        new_data
    )
    VALUES
    (
        h.building_id,
        'REVERT',
        now(),
        v_current,
        h.old_data
    );

END;
$$
LANGUAGE plpgsql;