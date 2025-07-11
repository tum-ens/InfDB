CREATE TABLE IF NOT EXISTS pylovo_input.ways (
    way_id                         SERIAL PRIMARY KEY,
    verkehrslinie_id_basemap  TEXT,
    clazz                      INTEGER,
    source                     INTEGER,
    target                     INTEGER,
    cost                       DOUBLE PRECISION,
    reverse_cost               DOUBLE PRECISION,
    geom                       geometry(LineString, 3035)
);

CREATE INDEX IF NOT EXISTS idx_ways_geom ON pylovo_input.ways USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_ways_verkehrslinie_id ON pylovo_input.ways (verkehrslinie_id_basemap);
CREATE INDEX IF NOT EXISTS idx_verkehrslinie_id ON basemap.verkehrslinie (id);

