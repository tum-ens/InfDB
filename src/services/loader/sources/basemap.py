import os
import geopandas as gpd
from src.services.loader import utils
from src.core import config
from src.services.loader import logger

log = logger.get_logger("infdb-loader")

def load():
    logger.init_logger("infdb-loader", "infdb-loader.log")
    log = logger.get_logger("infdb-loader")

    if not utils.if_active("basemap"):
        log.info("basemap skips, status not active")
        return

    log.info("Loading Basemap data...")

    # Create folders if they do not exist
    base_path = config.get_path(["loader", "sources", "basemap", "path", "base"])
    os.makedirs(base_path, exist_ok=True)

    # processed_path = config.get_path(["loader", "sources", "basemap", "path", "processed"])
    # os.makedirs(processed_path, exist_ok=True)

    site_url = config.get_value(["loader", "sources", "basemap", "url"])
    ending = config.get_value(["loader", "sources", "basemap", "ending"])
    filter = config.get_value(["loader", "sources", "basemap", "filter"])
    urls = utils.get_links(site_url, ending, filter)

    download_files = utils.download_files(urls, base_path)

    # Create schema if it doesn't exist
    schema = config.get_value(["loader", "sources", "basemap", "schema"])
    sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"
    utils.sql_query(sql)

    prefix = config.get_value(["loader", "sources", "basemap", "prefix"])

    for file in download_files:
        log.info(f"Loading {file}...")
        list = gpd.list_layers(file)["name"]
        print(list)
        layer_names = config.get_value(["loader", "sources", "basemap", "layer"])
        layers = [layer + "_bdlm" for layer in layer_names]
        utils.import_layers(file, layers, schema, prefix=prefix, layer_names=layer_names)