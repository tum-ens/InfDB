-- Create a temporary table with transformed geometry and spatial index
DROP TABLE IF EXISTS temp_grid_transformed;
CREATE TEMPORARY TABLE temp_grid_transformed AS
SELECT
    id,
    x_mp,
    y_mp,
    ST_Transform(geom, 3035) as geom
FROM opendata.bkg_de_grid_etrs89_laea_100m;

-- Create spatial index on transformed geometry (fixed column name)
CREATE INDEX temp_grid_geom_idx ON temp_grid_transformed USING GIST (geom);

-- Create table joining grid cells with buildings based on geometry
-- Only keeps grid cells that contain at least one building centroid
-- Optimized for later joins on x_mp and y_mp coordinates
DROP TABLE IF EXISTS pylovo_input.buildings_grid;
CREATE TABLE IF NOT EXISTS pylovo_input.buildings_grid AS
SELECT DISTINCT g.*
FROM temp_grid_transformed g
INNER JOIN pylovo_input.buildings b ON ST_Contains(g.geom, ST_Centroid(b.geom));

-- Create composite index on x_mp and y_mp for efficient joins
CREATE INDEX grid_buildings_spatial_coords_idx
    ON pylovo_input.buildings_grid (x_mp, y_mp);

-- Add all census columns to the existing buildings_grid table
ALTER TABLE pylovo_input.buildings_grid
-- cns22_100m_bevoelkerungszahl
ADD COLUMN einwohner bigint,
-- cns22_100m_durchschn_haushaltsgroesse
ADD COLUMN durchschnhhgroesse double precision,
ADD COLUMN werterlaeuternde_zeichen text,
-- cns22_100m_geb_gbdtyp_groesse
ADD COLUMN insgesamt_gebaeude bigint,
ADD COLUMN freiefh double precision,
ADD COLUMN efh_dhh double precision,
ADD COLUMN efh_reihenhaus double precision,
ADD COLUMN freist_zfh double precision,
ADD COLUMN zfh_dhh double precision,
ADD COLUMN zfh_reihenhaus double precision,
ADD COLUMN mfh_3bis6wohnungen double precision,
ADD COLUMN mfh_7bis12wohnungen double precision,
ADD COLUMN mfh_13undmehrwohnungen double precision,
ADD COLUMN anderergebaeudetyp double precision;

-- Update with population data
UPDATE pylovo_input.buildings_grid
SET einwohner = pop.einwohner
FROM opendata.cns22_100m_bevoelkerungszahl pop
WHERE buildings_grid.x_mp = pop.x_mp_100m
  AND buildings_grid.y_mp = pop.y_mp_100m;

-- Update with household size data
UPDATE pylovo_input.buildings_grid
SET durchschnhhgroesse = hh.durchschnhhgroesse,
    werterlaeuternde_zeichen = hh.werterlaeuternde_zeichen
FROM opendata.cns22_100m_durchschn_haushaltsgroesse hh
WHERE buildings_grid.x_mp = hh.x_mp_100m
  AND buildings_grid.y_mp = hh.y_mp_100m;

-- Update with building type data
UPDATE pylovo_input.buildings_grid
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
FROM opendata.cns22_100m_geb_gbdtyp_groesse bld
WHERE buildings_grid.x_mp = bld.x_mp_100m
  AND buildings_grid.y_mp = bld.y_mp_100m;
