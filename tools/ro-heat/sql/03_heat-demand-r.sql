DO $$
DECLARE
    v_changelog_id BIGINT;
BEGIN
-- create a new changelog id and store it in a variable for later reference in the insert statements
SELECT public.fn_begin_changelog('{tool_name}', 'no comment', session_user::TEXT, '{ags}', '{process_id}') INTO v_changelog_id;

-- DROP TABLE IF EXISTS {output_schema}.annual_heating_demand;

CREATE TABLE IF NOT EXISTS {output_schema}.annual_heating_demand (
    building_objectid text PRIMARY KEY,
    "heating:demand[kWh]" double precision,
    changelog_id      BIGINT REFERENCES public.changelog(id) ON DELETE SET NULL
);

INSERT INTO {output_schema}.annual_heating_demand (building_objectid, "heating:demand[kWh]", changelog_id)
    SELECT
        bldrc.building_objectid,
        -- simplified heat demand equation (6.4) in Patrick's phd thesis
        (count(ts.value)*1/bldrc.resistance)*({temp_in} - avg(ts.value))/1000 AS "heating:demand[kWh]",
        v_changelog_id
    FROM
        {output_schema}.buildings_rc AS bldrc
    JOIN
        basedata.bld2ts
        ON bldrc.building_objectid = basedata.bld2ts.bld_objectid
    JOIN
        opendata.openmeteo_ts_data AS ts
        ON basedata.bld2ts.ts_metadata_id = ts.ts_metadata_id
    JOIN opendata.openmeteo_ts_metadata
        ON ts.ts_metadata_id = opendata.openmeteo_ts_metadata.id
    JOIN basedata.buildings
        ON bldrc.building_objectid = basedata.buildings.objectid
    WHERE
        {temp_in} > ts.value AND    -- constraint of upper equation (Tin > Tout) for all time steps
        opendata.openmeteo_ts_metadata.name = 'openmeteo_hourly_temperature_2m'
        AND ts.time  >= '{start_time}'
        AND ts.time <  '{end_time}'
        AND basedata.buildings.gemeindeschluessel LIKE '{ags}'
    GROUP BY bldrc.building_objectid, bldrc.resistance
ON CONFLICT (building_objectid)
DO UPDATE SET
    "heating:demand[kWh]" = EXCLUDED."heating:demand[kWh]",
    changelog_id = EXCLUDED.changelog_id;

END;
$$;