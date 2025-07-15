ALTER TABLE pylovo_input.buildings ALTER COLUMN objectid SET NOT NULL;
ALTER TABLE pylovo_input.buildings ADD CONSTRAINT objectid_unique UNIQUE (objectid);

ALTER TABLE pylovo_input.buildings ALTER COLUMN building_use SET NOT NULL;
ALTER TABLE pylovo_input.buildings ADD CONSTRAINT building_use_check CHECK (building_use IN ('Residential', 'Industrial', 'Commercial', 'Public'));

ALTER TABLE pylovo_input.buildings ALTER COLUMN building_use_id SET NOT NULL;

ALTER TABLE pylovo_input.buildings ALTER COLUMN height SET NOT NULL;
ALTER TABLE pylovo_input.buildings ADD CONSTRAINT height_check CHECK (height > 0);

ALTER TABLE pylovo_input.buildings ALTER COLUMN geom SET NOT NULL;
ALTER TABLE pylovo_input.buildings ALTER COLUMN floor_area SET NOT NULL;
ALTER TABLE pylovo_input.buildings ADD CONSTRAINT floor_area_check CHECK (floor_area > 0);

ALTER TABLE pylovo_input.buildings ALTER COLUMN floor_number SET NOT NULL;
ALTER TABLE pylovo_input.buildings ADD CONSTRAINT floor_number_check CHECK (floor_number > 0);

ALTER TABLE pylovo_input.buildings ADD CONSTRAINT occupants_check CHECK (occupants >= 0);

ALTER TABLE pylovo_input.buildings ADD CONSTRAINT households_check CHECK (households >= 0);

--ALTER TABLE pylovo_input.buildings ALTER COLUMN construction_year SET NOT NULL;
--ALTER TABLE pylovo_input.buildings
--    ADD CONSTRAINT construction_year_check CHECK (construction_year IN
--                                                  ('-1919', '1919-1948', '1949-1978', '1979-1990', '1991-2000',
--                                                   '2001-2010', '2011-2019', '2020-'));

ALTER TABLE pylovo_input.buildings
    ADD CONSTRAINT building_type_check CHECK (building_type IN
                                              ('AB', 'MFH', 'TH', 'SFH'));

ALTER TABLE pylovo_input.buildings ALTER COLUMN postcode SET NOT NULL;
