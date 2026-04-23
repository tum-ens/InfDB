DO $$
DECLARE
    v_changelog_id BIGINT;
BEGIN
-- create a new changelog id and store it in a variable for later reference in the insert statements
SELECT public.fn_begin_changelog('{tool_name}', 'no comment', session_user::TEXT, '{ags}', '{process_id}') INTO v_changelog_id;

-- =========================================================
-- buildings (global)
-- =========================================================
DELETE FROM {output_schema}.buildings b
WHERE b.gemeindeschluessel = '{ags}';

INSERT INTO {output_schema}.buildings
SELECT * FROM temp_buildings;

UPDATE {output_schema}.buildings
SET changelog_id = v_changelog_id
WHERE gemeindeschluessel = '{ags}';

-- =========================================================
-- building_surface_area (global)
-- =========================================================
DELETE FROM {output_schema}.building_surface_area b
WHERE b.gemeindeschluessel = '{ags}';

INSERT INTO {output_schema}.building_surface_area
SELECT * FROM temp_building_surface;

-- =========================================================
-- buildings_grid_100m (global) UPSERT
-- =========================================================
INSERT INTO {output_schema}.buildings_grid_100m
SELECT * FROM temp_buildings_grid_100m
ON CONFLICT (id) DO UPDATE
SET
    x_mp = EXCLUDED.x_mp,
    y_mp = EXCLUDED.y_mp,
    geom = EXCLUDED.geom,
    einwohner = EXCLUDED.einwohner,
    durchschnhhgroesse = EXCLUDED.durchschnhhgroesse,
    werterlaeuternde_zeichen = EXCLUDED.werterlaeuternde_zeichen,
    insgesamt_gebaeude = EXCLUDED.insgesamt_gebaeude,
    freiefh = EXCLUDED.freiefh,
    efh_dhh = EXCLUDED.efh_dhh,
    efh_reihenhaus = EXCLUDED.efh_reihenhaus,
    freist_zfh = EXCLUDED.freist_zfh,
    zfh_dhh = EXCLUDED.zfh_dhh,
    zfh_reihenhaus = EXCLUDED.zfh_reihenhaus,
    mfh_3bis6wohnungen = EXCLUDED.mfh_3bis6wohnungen,
    mfh_7bis12wohnungen = EXCLUDED.mfh_7bis12wohnungen,
    mfh_13undmehrwohnungen = EXCLUDED.mfh_13undmehrwohnungen,
    anderergebaeudetyp = EXCLUDED.anderergebaeudetyp,
    vor1919 = EXCLUDED.vor1919,
    a1919bis1948 = EXCLUDED.a1919bis1948,
    a1949bis1978 = EXCLUDED.a1949bis1978,
    a1979bis1990 = EXCLUDED.a1979bis1990,
    a1991bis2000 = EXCLUDED.a1991bis2000,
    a2001bis2010 = EXCLUDED.a2001bis2010,
    a2011bis2019 = EXCLUDED.a2011bis2019,
    a2020undspaeter = EXCLUDED.a2020undspaeter,
    changelog_id = v_changelog_id;

-- =========================================================
-- buildings_grid_1km (global) UPSERT
-- =========================================================
INSERT INTO {output_schema}.buildings_grid_1km
SELECT * FROM temp_buildings_grid_1km
ON CONFLICT (id) DO UPDATE
SET
    x_mp = EXCLUDED.x_mp,
    y_mp = EXCLUDED.y_mp,
    geom = EXCLUDED.geom,
    einwohner = EXCLUDED.einwohner,
    durchschnhhgroesse = EXCLUDED.durchschnhhgroesse,
    werterlaeuternde_zeichen = EXCLUDED.werterlaeuternde_zeichen,
    insgesamt_gebaeude = EXCLUDED.insgesamt_gebaeude,
    freiefh = EXCLUDED.freiefh,
    efh_dhh = EXCLUDED.efh_dhh,
    efh_reihenhaus = EXCLUDED.efh_reihenhaus,
    freist_zfh = EXCLUDED.freist_zfh,
    zfh_dhh = EXCLUDED.zfh_dhh,
    zfh_reihenhaus = EXCLUDED.zfh_reihenhaus,
    mfh_3bis6wohnungen = EXCLUDED.mfh_3bis6wohnungen,
    mfh_7bis12wohnungen = EXCLUDED.mfh_7bis12wohnungen,
    mfh_13undmehrwohnungen = EXCLUDED.mfh_13undmehrwohnungen,
    anderergebaeudetyp = EXCLUDED.anderergebaeudetyp,
    vor1919 = EXCLUDED.vor1919,
    a1919bis1948 = EXCLUDED.a1919bis1948,
    a1949bis1978 = EXCLUDED.a1949bis1978,
    a1979bis1990 = EXCLUDED.a1979bis1990,
    a1991bis2000 = EXCLUDED.a1991bis2000,
    a2001bis2010 = EXCLUDED.a2001bis2010,
    a2011bis2019 = EXCLUDED.a2011bis2019,
    a2020undspaeter = EXCLUDED.a2020undspaeter,
    changelog_id = v_changelog_id;

-- -- =========================================================
-- -- bld2grid (global) UPSERT
-- -- =========================================================
-- INSERT INTO {output_schema}.bld2grid
-- SELECT * FROM temp_bld2grid
-- ON CONFLICT (objectid, id) DO UPDATE
-- SET
--     resolution_meters = EXCLUDED.resolution_meters;

-- =========================================================
-- bld2ts (global) UPSERT
-- =========================================================
INSERT INTO {output_schema}.bld2ts (bld_objectid, ts_metadata_id, ts_metadata_name, dist, geom, changelog_id)
SELECT bld_objectid, ts_metadata_id, ts_metadata_name, dist, geom, v_changelog_id
FROM temp_bld2ts
ON CONFLICT (bld_objectid, ts_metadata_name) DO UPDATE
SET
    ts_metadata_id = EXCLUDED.ts_metadata_id,
    dist           = EXCLUDED.dist,
    geom           = EXCLUDED.geom,
    changelog_id   = v_changelog_id;


-- =========================================================
-- cleanup (per-container)
-- =========================================================
DROP TABLE IF EXISTS temp_buildings;
DROP TABLE IF EXISTS temp_buildings_grid_100m;
DROP TABLE IF EXISTS temp_buildings_grid_1km;
-- DROP TABLE IF EXISTS temp_bld2grid;
DROP TABLE IF EXISTS temp_bld2ts;
DROP TABLE IF EXISTS temp_building_surface;

END;
$$;