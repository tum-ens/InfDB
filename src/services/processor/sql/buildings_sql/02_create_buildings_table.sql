DROP TABLE IF EXISTS pylovo_input.buildings;
CREATE TABLE pylovo_input.buildings
(
    id                bigint PRIMARY KEY,
    objectid          text UNIQUE NOT NULL,
    height            double precision,
    floor_area        double precision,
    floor_number      int,
    building_use      text NOT NULL,
    building_use_id   text NOT NULL,
    building_type     text,
    occupants         int,
    households        int,
    construction_year text,
    postcode          int,
    address_street_id bigint,
    geom              geometry(MultiPolygon, 3035)
);

CREATE INDEX IF NOT EXISTS building_geom_idx ON pylovo_input.buildings USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_building_type_check ON pylovo_input.buildings (id, building_type, building_use);
