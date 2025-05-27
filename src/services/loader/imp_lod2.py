from src.services.loader import utils
from src.core.config import config
import os


def imp_lod2():
    status = config["opendata"]["lod2"]["status"]
    if status != "active":
        print("imp_lod skips, status not active")
        return

    base_path = config["opendata"]["lod2"]["lod2_dir"]
    os.makedirs(base_path, exist_ok=True)

    # Run aria2c to download the file (equivalent to `aria2c <url>`)
    url = config["opendata"]["lod2"]["url"]
    if isinstance(url, list):
        url = (" ").join(url)

    gml_path = config["opendata"]["lod2"]["gml_dir"]
    cmd = f"aria2c --continue=true --allow-overwrite=false --auto-file-renaming=false {url} -d {gml_path}"
    os.system(cmd)

    ## Import *gml files into 3D-CDB
    user = utils.citydb_user
    password = utils.citydb_password
    port = utils.citydb_port
    host = utils.citydb_host
    database = utils.citydb_db

    cmd = f"citydb import citygml -H {host} -P {port} -d {database} -u {user} -p {password} {gml_path}/*.gml"
    utils.do_cmd(cmd)

    ## Extract general information like envelope
    schema = config["general"]["schema"]
    epsg = config["citydb"]["epsg"]
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
