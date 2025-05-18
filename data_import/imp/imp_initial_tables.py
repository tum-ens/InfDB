from data_import.imp import config, utils


def import_schemas():
    ## Extract general information like envelope
    schema = config.get_value(["general", "schema"])
    epsg = config.epsg
    sql = f"""
            DROP SCHEMA IF EXISTS {schema} CASCADE;
            CREATE SCHEMA IF NOT EXISTS {schema};
            CREATE TABLE {schema}.buildings AS
            SELECT feature.id as feature_id, geometry
            FROM feature
                     JOIN property ON feature.id = property.feature_id
                     JOIN geometry_data on feature.id =geometry_data.feature_id
                     JOIN objectclass ON feature.objectclass_id = objectclass.id
            WHERE objectclass.classname = 'GroundSurface';
            CREATE INDEX IF NOT EXISTS idx_buildings_geometry ON {schema}.buildings USING GIST (geometry);
            CREATE TABLE {schema}.envelope AS
            SELECT ST_Envelope(ST_Union(geometry)) as geometry
            FROM {schema}.buildings;

            CREATE TABLE {schema}.envelopefast AS
            SELECT ST_MakeEnvelope(
                   ST_XMin(ST_Extent(geometry)),
                   ST_YMin(ST_Extent(geometry)),
                   ST_XMax(ST_Extent(geometry)),
                   ST_YMax(ST_Extent(geometry)),
               -- Optionally, specify the SRID of your geometries
               -- For example, 4326 for WGS 84 
               {epsg}
           ) as bounding_polygon
    FROM {schema}.buildings;
    """

    utils.sql_query(sql)


import_schemas()
