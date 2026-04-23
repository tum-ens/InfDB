-- Summary: Prepares the buildings_grid table by spatially joining grid cells
-- with building centroids. It enriches the grid with census data including
-- population, household size, building type distribution, and construction
-- year statistics.

-- Create temp table joining grid cells with buildings based on geometry
-- Only keeps grid cells that contain at least one building centroid
-- Optimized for later joins on x_mp and y_mp coordinates

-- Prepare building grid cells

-- fill grid_cells temp table
INSERT INTO temp_grid_cells (id, x_mp, y_mp, name, resolution_meters, geom)
SELECT
    g.id,
    g.x_mp,
    g.y_mp,
    g.name,
    g.resolution_meters,
    ST_Transform(g.geom, {EPSG}) as geom
FROM {input_schema}.grid_cells g
    JOIN {input_schema}.bkg_vg5000_gem bkg ON bkg.ags = '{ags}' AND ST_Intersects(g.geom, bkg.geom)
WHERE EXISTS (
    SELECT 1
    FROM {input_schema}.building_view b
    WHERE g.geom && b.geom
      AND ST_Contains(g.geom, b.centroid)
      AND b.gemeindeschluessel = '{ags}'
);

-- 100m building grid raster (write into temp table)
INSERT INTO temp_buildings_grid_100m (id, x_mp, y_mp, geom)
SELECT
    g.id,
    g.x_mp,
    g.y_mp,
    g.geom
FROM temp_grid_cells g
WHERE name='DE_Grid_ETRS89_LAEA_100m';

-- 1km building grid raster (write into temp table)
INSERT INTO temp_buildings_grid_1km (id, x_mp, y_mp, geom)
SELECT
    g.id,
    g.x_mp,
    g.y_mp,
    g.geom
FROM temp_grid_cells g
WHERE name='DE_Grid_ETRS89_LAEA_1km';

ANALYZE temp_buildings_grid_100m;

-- Add zensus data to grid cells
-- Update with population data
UPDATE temp_buildings_grid_100m
SET einwohner = pop.einwohner
FROM {input_schema}.zensus_2022_100m_bevoelkerungszahl pop
WHERE temp_buildings_grid_100m.x_mp = pop.x_mp_100m
  AND temp_buildings_grid_100m.y_mp = pop.y_mp_100m;

-- Update with household size data
UPDATE temp_buildings_grid_100m
SET durchschnhhgroesse = hh.durchschnhhgroesse,
    werterlaeuternde_zeichen = hh.werterlaeuternde_zeichen
FROM {input_schema}.zensus_2022_100m_durchschn_haushaltsgroesse hh
WHERE temp_buildings_grid_100m.x_mp = hh.x_mp_100m
  AND temp_buildings_grid_100m.y_mp = hh.y_mp_100m;

-- Update with construction year data
UPDATE temp_buildings_grid_100m
SET vor1919 = bauj.vor1919,
  a1919bis1948 = bauj.a1919bis1948,
  a1949bis1978 = bauj.a1949bis1978,
  a1979bis1990 = bauj.a1979bis1990,
  a1991bis2000 = bauj.a1991bis2000,
  a2001bis2010 = bauj.a2001bis2010,
  a2011bis2019 = bauj.a2011bis2019,
  a2020undspaeter = bauj.a2020undspaeter
FROM {input_schema}.zensus_2022_100m_gebaeude_baujahr_mikrozensus bauj
WHERE temp_buildings_grid_100m.x_mp = bauj.x_mp_100m
  AND temp_buildings_grid_100m.y_mp = bauj.y_mp_100m;

-- Update with building type data conditional on the resolution variable
UPDATE temp_buildings_grid_{census_building_type_resolution}
SET insgesamt_gebaeude = bld.insgesamt_gebaeude,
  freiefh = bld.freiefh,
  efh_dhh = bld.efh_dhh,
  efh_reihenhaus = bld.efh_reihenhaus,
  freist_zfh = bld.freist_zfh,
  zfh_dhh = bld.zfh_dhh,
  zfh_reihenhaus = bld.zfh_reihenhaus,
  mfh_3bis6wohnungen = bld.mfh_3bis6wohnungen,
  mfh_7bis12wohnungen = bld.mfh_7bis12wohnungen,
  mfh_13undmehrwohnungen = bld.mfh_13undmehrwohnungen,
  anderergebaeudetyp = bld.anderergebaeudetyp
FROM {input_schema}.zensus_2022_{census_building_type_resolution}_gebaeude_typ_groesse bld
WHERE temp_buildings_grid_{census_building_type_resolution}.x_mp = bld.x_mp_{census_building_type_resolution}
  AND temp_buildings_grid_{census_building_type_resolution}.y_mp = bld.y_mp_{census_building_type_resolution};
