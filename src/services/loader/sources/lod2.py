from src.services.loader import utils, logger
from src.core import config
import os

log = logger.get_logger("infdb-loader")

def load():
    logger.init_logger("infdb-loader", "infdb-loader.log")
    log = logger.get_logger("infdb-loader")

    if not utils.if_active("zensus_2022"):
        log.info("zensus_2022 skips, status not active")
        return

    base_path = config.get_path(["loader", "sources", "lod2", "path", "lod2"])
    os.makedirs(base_path, exist_ok=True)

    # Run aria2c to download the file (equivalent to `aria2c <url>`)
    url = config.get_value(["loader", "sources", "lod2", "url"])
    if isinstance(url, list):
        url = (" ").join(url)

    gml_path = config.get_path(["loader", "sources", "lod2", "path", "gml"])
    cmd = f"aria2c --continue=true --allow-overwrite=false --auto-file-renaming=false {url} -d {gml_path}"
    utils.do_cmd(cmd)

    ## Import *gml files into 3D-CDB
    host, port, user, password, db = utils.get_db_config("citydb")
    # epsg = config.get_value(["services", "citydb", "epsg"])

    # cmd = f"citydb import citygml -H {host} -P {port} -d {db} -u {user} -p {password} {gml_path}/*.gml"
    # utils.do_cmd(cmd)

    # ## Extract general information like envelope
    # schema = config.get_value(["base", "schema"])
    # sql = f"""
    #         DROP SCHEMA IF EXISTS {schema} CASCADE;
    #         CREATE SCHEMA IF NOT EXISTS {schema};
    #         CREATE TABLE {schema}.buildings AS
    #         SELECT feature.id as feature_id, geometry
    #         FROM feature
    #                  JOIN property ON feature.id = property.feature_id
    #                  JOIN geometry_data on feature.id =geometry_data.feature_id
    #                  JOIN objectclass ON feature.objectclass_id = objectclass.id
    #         WHERE objectclass.classname = 'GroundSurface';
    #         CREATE INDEX IF NOT EXISTS idx_buildings_geometry ON {schema}.buildings USING GIST (geometry);
    #         CREATE TABLE {schema}.envelope AS
    #         SELECT ST_Envelope(ST_Union(geometry)) as geometry
    #         FROM {schema}.buildings;
    #
    #         CREATE TABLE {schema}.envelopefast AS
    #         SELECT ST_MakeEnvelope(
    #                ST_XMin(ST_Extent(geometry)),
    #                ST_YMin(ST_Extent(geometry)),
    #                ST_XMax(ST_Extent(geometry)),
    #                ST_YMax(ST_Extent(geometry)),
    #            -- Optionally, specify the SRID of your geometries
    #            -- For example, 4326 for WGS 84
    #            {epsg}
    #        ) as bounding_polygon
    # FROM {schema}.buildings;
    # """
    #
    # utils.sql_query(sql)
