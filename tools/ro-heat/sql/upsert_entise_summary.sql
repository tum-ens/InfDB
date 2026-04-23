CREATE TABLE IF NOT EXISTS {output_schema}.entise_summary
(
    building_objectid TEXT PRIMARY KEY,
    "heating:demand[Wh]" DOUBLE PRECISION,
    "heating:load_max[W]" DOUBLE PRECISION,
    "cooling:demand[Wh]" DOUBLE PRECISION,
    "cooling:load_max[W]" DOUBLE PRECISION
);

INSERT INTO {output_schema}.entise_summary (
    building_objectid,
    "heating:demand[Wh]",
    "heating:load_max[W]",
    "cooling:demand[Wh]",
    "cooling:load_max[W]"
)
SELECT
    building_objectid,
    "heating:demand[Wh]",
    "heating:load_max[W]",
    "cooling:demand[Wh]",
    "cooling:load_max[W]"
FROM {output_schema}.temp_entise_summary_{ags}
ON CONFLICT (building_objectid)
DO UPDATE SET "heating:demand[Wh]" = EXCLUDED."heating:demand[Wh]",
"heating:load_max[W]" = EXCLUDED."heating:load_max[W]",
"cooling:demand[Wh]" = EXCLUDED."cooling:demand[Wh]",
"cooling:load_max[W]" = EXCLUDED."cooling:load_max[W]";

DROP table {output_schema}.temp_entise_summary_{ags};