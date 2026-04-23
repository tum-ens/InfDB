-- 6. View Erstellung
-- WARNUNG: Materialized Views verdoppeln den Speicherbedarf. 
-- Wenn diese Daten nicht ständig aktualisiert werden, ist eine "CREATE TABLE AS" besser.
DROP MATERIALIZED VIEW IF EXISTS {output_schema}.{bld_table_name}_view; -- Drop View statt Table
DROP TABLE IF EXISTS {output_schema}.{bld_table_name}_view;

-- Wir nutzen CREATE TABLE statt Materialized View für bessere Performance beim Erstellen
CREATE TABLE {output_schema}.{bld_table_name}_view AS
SELECT 
    bld.*,
    sur.area AS groundsurface_flaeche,
    ST_Multi(sur.geom) AS geom,
    -- ST_PointOnSurface ist oft schneller und sicherer (garantiert im Polygon) als Centroid für Building-Footprints
    ST_PointOnSurface(sur.geom) AS centroid 
FROM {output_schema}.building_lod2 bld
JOIN {output_schema}.{bld_table_name}_surface sur ON bld.objectid = sur.building_objectid
WHERE sur.objectclass_id = 710; -- 710 = ground surface

-- Indizes für den View (wie in Ihrem Original, aber GIST für Centroid hinzugefügt)
CREATE INDEX IF NOT EXISTS {bld_table_name}_view_objectid_idx ON {output_schema}.{bld_table_name}_view (objectid);
CREATE INDEX IF NOT EXISTS {bld_table_name}_view_geom_idx ON {output_schema}.{bld_table_name}_view USING GIST (geom);
-- ... (restliche Indizes hier einfügen)