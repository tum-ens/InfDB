import os
import logging
import geopandas as gpd
from . import utils, config, logger

log = logging.getLogger(__name__)

def load(log_queue):
    logger.setup_worker_logger(log_queue)

    if not utils.if_active("basemap"):
        return

    # Create folders if they do not exist
    base_path = config.get_path(["loader", "sources", "basemap", "path", "base"])
    os.makedirs(base_path, exist_ok=True)

    # processed_path = config.get_path(["loader", "sources", "basemap", "path", "processed"])
    # os.makedirs(processed_path, exist_ok=True)

    site_url = config.get_value(["loader", "sources", "basemap", "url"])
    ending = config.get_value(["loader", "sources", "basemap", "ending"])
    filters = config.get_value(["loader", "sources", "basemap", "filter"])
    
    for filter in filters:
        urls = utils.get_links(site_url, ending, filter)

        log.debug(urls)
        download_files = utils.download_files(urls, base_path)
        log.debug(f"Download_files: {download_files}")

        # Create schema if it doesn't exist
        schema = config.get_value(["loader", "sources", "basemap", "schema"])
        sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"
        utils.sql_query(sql)

        prefix = config.get_value(["loader", "sources", "basemap", "prefix"])
        log.debug(f"Using prefix: {prefix}")

        file = utils.get_file(base_path, filter, ".gpkg")

        log.info(f"Loading {file}...")
        # list = gpd.list_layers(file)["name"]
        # print(list)
        layer_names = config.get_value(["loader", "sources", "basemap", "layer"])
        layers = [layer + "_bdlm" for layer in layer_names]
        utils.import_layers(file, layers, schema, prefix=prefix, layer_names=layer_names) #TODO: Add if several files

        log.info(f"Basemap data loaded successfully")
