CREATE SCHEMA IF NOT EXISTS {output_schema};
DROP TABLE IF EXISTS {output_schema}.{table_name};
CREATE TABLE IF NOT EXISTS {output_schema}.{table_name}
(
    id                SERIAL,
    ags_id TEXT,
    feature_id        integer,
    objectid          text,
    gemeindeschluessel text,
    objectclass_id    int,
    height            double precision,
    -- groundsurface_flaeche        double precision,
    storeysaboveground      integer,
    -- building_use      text NOT NULL,
    building_function_code   text NOT NULL,
    -- building_type     text,
    -- occupants         int,
    -- households        int,
    -- construction_year text,
    zip_code          text,
    street            text,
    house_number     text,
    city              text,
    country          text,
    state            text,
    -- geom              geometry,
    -- centroid          geometry,
    changelog_id      BIGINT REFERENCES public.changelog(id) ON DELETE SET NULL,
    PRIMARY KEY (id, ags_id)
) PARTITION BY LIST (ags_id);

-- CREATE INDEX IF NOT EXISTS building_geom_idx ON {output_schema}.{table_name} USING GIST (geom);
-- CREATE INDEX IF NOT EXISTS building_centroid_idx ON {output_schema}.{table_name} USING GIST (centroid);
CREATE INDEX IF NOT EXISTS building_function_code_idx ON {output_schema}.{table_name} (building_function_code);
CREATE INDEX IF NOT EXISTS building_lod2_feature_id_idx ON {output_schema}.{table_name} (feature_id);
CREATE INDEX IF NOT EXISTS building_lod2_gks_objectid_idx ON {output_schema}.{table_name} (gemeindeschluessel);
CREATE INDEX IF NOT EXISTS building_lod2_objectid_idx ON {output_schema}.{table_name} (objectid);
CREATE INDEX IF NOT EXISTS building_lod2_ags_id_idx ON {output_schema}.{table_name} (ags_id);
CREATE INDEX IF NOT EXISTS building_lod2_changelog_id_idx ON {output_schema}.{table_name} (changelog_id);