DROP TABLE IF EXISTS {output_schema}.buildings;
CREATE TABLE {output_schema}.buildings
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
    geom              geometry(MultiPolygon, 3035),
    centroid          geometry(Point, 3035)
);

CREATE INDEX IF NOT EXISTS building_geom_idx ON {output_schema}.buildings USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_building_type_check ON {output_schema}.buildings (id, building_type, building_use);
