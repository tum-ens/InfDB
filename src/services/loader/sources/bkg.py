import os
from src.services.loader import utils, logger
from src.core import config

log = logger.get_logger("infdb-loader")

def load():
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

    # Base path for processed files
    processed_path = config.get_path(["loader", "sources", "bkg", "path", "processed"])
    os.makedirs(processed_path, exist_ok=True)

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
    # # ToDo: loop for resolution
    # # 1km
    # print("Downloading and unzipping Geogitter")
    # geogitter_zip = os.path.join(zip_path, "DE_Grid_ETRS89-LAEA_1km.gpkg.zip")
    # download_and_unzip("https://daten.gdz.bkg.bund.de/produkte/sonstige/geogitter/aktuell/DE_Grid_ETRS89-LAEA_1km.gpkg.zip",
    #                    geogitter_zip, unzip_path)
    #
    # geogitter_1km_gpkg = os.path.join(unzip_path, "DE_Grid_ETRS89-LAEA_1km.gpkg/geogitter/DE_Grid_ETRS89-LAEA_1km.gpkg")
    # geogitter_1km_layers = ["de_grid_laea_1km"]
    # import_layers(geogitter_1km_gpkg, geogitter_1km_layers)
    #
    # # 10km
    # geogitter_zip = os.path.join(zip_path, "DE_Grid_ETRS89-LAEA_10km.gpkg.zip")
    # download_and_unzip("https://daten.gdz.bkg.bund.de/produkte/sonstige/geogitter/aktuell/DE_Grid_ETRS89-LAEA_10km.gpkg.zip",
    #                    geogitter_zip, unzip_path)
    #
    # geogitter_10km_gpkg = os.path.join(unzip_path, "DE_Grid_ETRS89-LAEA_10km.gpkg/geogitter/DE_Grid_ETRS89-LAEA_10km.gpkg")
    # geogitter_10km_layers = ["de_grid_laea_10km"]
    # import_layers(geogitter_10km_gpkg, geogitter_10km_layers)
    #
    # # 100m
    # geogitter_zip = os.path.join(zip_path, "DE_Grid_ETRS89-LAEA_100m.gpkg.zip")
    # download_and_unzip("https://daten.gdz.bkg.bund.de/produkte/sonstige/geogitter/aktuell/DE_Grid_ETRS89-LAEA_100m.gpkg.zip",
    #                    geogitter_zip, unzip_path)
    #
    # geogitter_100m_gpkg = os.path.join(unzip_path, "DE_Grid_ETRS89-LAEA_100m/geogitter/DE_Grid_ETRS89-LAEA_100m.gpkg")
    # geogitter_100m_layers = ["de_grid_laea_100m"]
    # import_layers(geogitter_100m_gpkg, geogitter_100m_layers)

    # ToDo: Remove temporary files
