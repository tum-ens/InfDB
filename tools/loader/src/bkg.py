import os
from . import config, utils
from .logger import setup_worker_logger
import logging

log = logging.getLogger(__name__)

def create_folders():
    ## Check if the required directories exist, if not create them
    # Base path for zip files
    zip_path = config.get_path(["loader", "sources", "bkg", "path", "zip"])
    os.makedirs(zip_path, exist_ok=True)

    # Base path for unzipped files
    unzip_path = config.get_path(["loader", "sources", "bkg", "path", "unzip"])
    os.makedirs(unzip_path, exist_ok=True)

    # # Base path for processed files
    # processed_path = config.get_path(["loader", "sources", "bkg", "path", "processed"])
    # os.makedirs(processed_path, exist_ok=True)

    # Create database connection
    ## Create schema in database
    schema = config.get_value(["loader", "sources", "bkg", "schema"])

    # Prefix for table names
    prefix = config.get_value(["loader", "sources", "bkg", "prefix"])

    return zip_path, unzip_path, schema, prefix


def load_envelop():
    zip_path, unzip_path, schema, prefix = create_folders()

    # Download envelope
    log.info("Downloading and unzipping envelope...")
    url = config.get_value(["loader", "sources", "bkg", "vg5000", "url"])
    files = utils.download_files(url, zip_path)
    utils.unzip(files, unzip_path)


def create_geogitter(resolution, epsg, schema, prefix):

    if resolution.endswith("km"):
        resolution_meters = int(resolution[:-2]) * 1000
    elif resolution.endswith("m"):
        resolution_meters = int(resolution[:-1])

    envelop = utils.get_envelop()
    wkt = envelop.to_crs(3035).unary_union.wkt

    sql = f"""
        DROP TABLE IF EXISTS {schema}.{prefix}_DE_Grid_ETRS89_LAEA_{resolution};
        CREATE TABLE {schema}.{prefix}_DE_Grid_ETRS89_LAEA_{resolution} AS
        WITH params AS (
            SELECT {resolution_meters}::int AS cell_size
        ),
            boundary AS (
                SELECT ST_GeomFromText('{wkt}', 3035) AS geom
            ),
             envelope AS (
                 SELECT
                     FLOOR(ST_XMin(b.geom) / p.cell_size) * p.cell_size AS x_min,
                     FLOOR(ST_YMin(b.geom) / p.cell_size) * p.cell_size AS y_min,
                     CEIL(ST_XMax(b.geom) / p.cell_size) * p.cell_size AS x_max,
                     CEIL(ST_YMax(b.geom) / p.cell_size) * p.cell_size AS y_max,
                     p.cell_size
                 FROM boundary b, params p
             ),
             grid_raw AS (
                 SELECT (ST_SquareGrid(
                         e.cell_size,
                         ST_MakeEnvelope(e.x_min, e.y_min, e.x_max, e.y_max, 3035)
                         )).*
                 FROM envelope e
             ),
             grid AS (
                 SELECT
                     ST_Transform(geom, {epsg}) AS geom,
                     ST_XMin(geom) AS x,
                     ST_YMin(geom) AS y
                 FROM grid_raw
             ),
             id_named AS (
                 SELECT
                     FORMAT(
                             '%sN%sE%s',
                             '{resolution}',
                              g.y::int::text,
                              g.x::int::text
                     ) AS id,
                     (g.x + (p.cell_size / 2.0))::int AS x_mp,
                     (g.y + (p.cell_size / 2.0))::int AS y_mp,
                     g.geom
                 FROM grid g, params p
             )
        SELECT *
        FROM id_named;
    """
    utils.sql_query(sql)


def load(log_queue):
    setup_worker_logger(log_queue)

    if not utils.if_active("bkg"):
        return

    zip_path, unzip_path, schema, prefix = create_folders()

    sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"
    utils.sql_query(sql)

    # NUTS-Gebiete
    log.info("Downloading and unzipping NUTS")
    url = config.get_value(["loader", "sources", "bkg", "nuts", "url"])
    files = utils.download_files(url, zip_path)
    utils.unzip(files, unzip_path)
    nuts_layers = config.get_value(["loader", "sources", "bkg", "nuts", "layer"])
    file = utils.get_file(unzip_path, filename="nuts250", ending=".gpkg")
    utils.import_layers(file, nuts_layers, schema, prefix)

    # Verwaltungsgebiete
    vg_layers = config.get_value(["loader", "sources", "bkg", "vg5000", "layer"])
    file = utils.get_file(unzip_path, filename="vg5000", ending=".gpkg")
    utils.import_layers(file, vg_layers, schema, prefix)

    # # Geogitter
    log.info("Creating Geogitter layers")
    resolutions = config.get_value(["loader", "sources", "bkg", "geogitter", "resolutions"])

    for resolution in resolutions:
        log.info(f"Creating Geogitter for resolution {resolution}")
        epsg = utils.get_db_parameters("citydb")["epsg"]
        create_geogitter(resolution, epsg, schema, prefix)

    log.info(f"BKG data loaded successfully")
