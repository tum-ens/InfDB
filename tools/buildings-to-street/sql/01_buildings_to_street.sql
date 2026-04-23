-- Assign buildings to the closest street
-- Parameters:
-- {streets_schema}, {streets_table}, {streets_id_expr}, {streets_geom}
-- {buildings_schema}, {buildings_table}, {buildings_id_expr}, {buildings_geom}
-- {output_schema}, {output_table}

CREATE SCHEMA IF NOT EXISTS {output_schema};
CREATE TABLE IF NOT EXISTS {output_schema}.{output_table} (
    building_id TEXT PRIMARY KEY,
    street_id TEXT,
    nearest_distance DOUBLE PRECISION,
    gemeindeschluessel TEXT,
    geom GEOMETRY
);

INSERT INTO {output_schema}.{output_table} (building_id, street_id, nearest_distance, gemeindeschluessel, geom)
SELECT
    {buildings_id_expr} AS building_id,
    {streets_id_expr} AS street_id,
    ST_Distance(b.{buildings_geom}, s.{streets_geom}) AS nearest_distance,
    b.gemeindeschluessel,
    ST_ShortestLine(b.{buildings_geom}, s.{streets_geom}) AS geom
FROM
    {buildings_schema}.{buildings_table} b
JOIN LATERAL (
    SELECT s.*
    FROM {streets_schema}.{streets_table} s
    WHERE ST_DWithin(s.{streets_geom}, b.{buildings_geom}, 100)
    ORDER BY b.{buildings_geom} <-> s.{streets_geom}
    LIMIT 1
) s ON true
WHERE b.gemeindeschluessel = '{ags}'
ON CONFLICT (building_id) DO UPDATE SET
    street_id = EXCLUDED.street_id,
    nearest_distance = EXCLUDED.nearest_distance,
    gemeindeschluessel = EXCLUDED.gemeindeschluessel,
    geom = EXCLUDED.geom;