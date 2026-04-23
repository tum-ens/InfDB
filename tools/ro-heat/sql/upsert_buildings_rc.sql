DO $$
DECLARE
    v_changelog_id BIGINT;
BEGIN

-- create a new changelog id and store it in a variable for later reference in the insert statements
SELECT public.fn_begin_changelog('{tool_name}', 'no comment', session_user::TEXT, '{ags}', '{process_id}') INTO v_changelog_id;

CREATE TABLE IF NOT EXISTS {output_schema}.buildings_rc
(
    building_objectid TEXT PRIMARY KEY,
    resistance DOUBLE PRECISION,
    capacitance DOUBLE PRECISION,
    changelog_id      BIGINT REFERENCES public.changelog(id) ON DELETE SET NULL
);

INSERT INTO {output_schema}.buildings_rc (building_objectid,
                                          resistance,
                                          capacitance,
                                          changelog_id)
SELECT building_objectid,
       resistance,
       capacitance,
       v_changelog_id
FROM {output_schema}.temp_buildings_rc_{ags}
ON CONFLICT (building_objectid)
DO UPDATE SET resistance = EXCLUDED.resistance,
capacitance = EXCLUDED.capacitance,
changelog_id = EXCLUDED.changelog_id;

DROP table {output_schema}.temp_buildings_rc_{ags};

END;
$$;