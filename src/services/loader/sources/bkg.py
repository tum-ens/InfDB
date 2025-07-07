import os
from src.services.loader import utils, logger
from src.core import config

log = logger.get_logger("infdb-loader")


def load():
    logger.init_logger("infdb-loader", "infdb-loader.log")
    log = logger.get_logger("infdb-loader")

    if not utils.if_active("bkg"):
        log.info("bkg skips, status not active")
        return

    log.info("Loading BKG data...")

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
    sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"
    utils.sql_query(sql)

    # Prefix for table names
    prefix = config.get_value(["loader", "sources", "bkg", "prefix"])

    # NUTS-Gebiete
    log.info("Downloading and unzipping NUTS")
    url = config.get_value(["loader", "sources", "bkg", "nuts", "url"])
    files = utils.download_files(url, zip_path)
    utils.unzip(files, unzip_path)
    nuts_layers = config.get_value(["loader", "sources", "bkg", "nuts", "layer"])
    utils.import_layers(os.path.join(unzip_path, "nuts250_12-31.utm32s.gpkg/nuts250_1231/DE_NUTS250.gpkg"), nuts_layers, schema, prefix)

    # Verwaltungsgebiete
    log.info("Downloading and unzipping Verwaltungsgebiete")
    url = config.get_value(["loader", "sources", "bkg", "vg500", "url"])
    files = utils.download_files(url, zip_path)
    utils.unzip(files, unzip_path)
    vg_layers = config.get_value(["loader", "sources", "bkg", "vg500", "layer"])
    utils.import_layers(os.path.join(unzip_path, "vg5000_12-31.utm32s.gpkg.ebenen/vg5000_ebenen_1231/DE_VG5000.gpkg"), vg_layers, schema, prefix)

    # # Geogitter
    log.info("Creating Geogitter layers")
    resolutions = config.get_value(["loader", "sources", "bkg", "geogitter", "resolutions"])

    for resolution in resolutions:
        log.info(f"Creating Geogitter for resolution {resolution}")
        create_geogitter(resolution)


def create_geogitter(resolution):

    scope = config.get_value(["base", "scope"])
    epsg = config.get_value(["services", "citydb", "epsg"])
    schema = config.get_value(["loader", "sources", "bkg", "schema"])
    prefix = config.get_value(["loader", "sources", "bkg", "prefix"])

    if resolution.endswith("km"):
        resolution_meters = int(resolution[:-2]) * 1000
    elif resolution.endswith("m"):
        resolution_meters = int(resolution[:-1])

    sql = f"""
        DROP TABLE IF EXISTS {schema}.{prefix}_DE_Grid_ETRS89_LAEA_{resolution};
        CREATE TABLE {schema}.{prefix}_DE_Grid_ETRS89_LAEA_{resolution} AS
        WITH params AS (
            SELECT {resolution_meters}::int AS cell_size  -- 🛠️ change this to 10000 for 10km, etc.
        ),
             boundary AS (
                 SELECT ST_Union(ST_Transform(geometry, 3035)) AS geom
                 FROM opendata.bkg_nuts250_n3
                 WHERE "NUTS_CODE" LIKE '{scope}%'
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
                              FLOOR(g.y / p.cell_size)::int::text,
                              FLOOR(g.x / p.cell_size)::int::text
                     ) AS id,
                     g.geom
                 FROM grid g, params p
             )
        SELECT *
        FROM id_named;
    """
    utils.sql_query(sql)
