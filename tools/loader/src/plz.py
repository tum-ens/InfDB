import os
import logging
from . import utils, config, logger

log = logging.getLogger(__name__)

def load(log_queue):
    logger.setup_worker_logger(log_queue)

    if not utils.if_active("plz"):
        return

    base_path = config.get_value(["loader", "sources", "plz", "path", "base"])
    log.debug(f"base_path={base_path}")
    os.makedirs(base_path, exist_ok=True)

    # processed_path = config.get_path(["loader", "sources", "plz", "path", "processed"])
    # os.makedirs(processed_path, exist_ok=True)

    url = config.get_value(["loader", "sources", "plz", "url"])
    log.debug(f"url={url}")
    filename, name, extension = utils.get_file_from_url(url)

    file_path = os.path.join(base_path, filename)
    log.debug(f"Downloading PLZ data from {url} to {file_path}")

    if os.path.exists(file_path):
        log.info(f"File {file_path} already exists.")
    else:
        # Download file
        log.info(f"File {file_path} will be downloaded from {url}")

        utils.download_files(url, base_path)

    schema = config.get_value(["loader", "sources", "plz", "schema"])

    # Create schema if it doesn't exist
    sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"
    utils.sql_query(sql)

    prefix = config.get_value(["loader", "sources", "plz", "prefix"])
    layers = config.get_value(["loader", "sources", "plz", "layer"])

    log.info(f"Loading PLZ data from {url} to {file_path}")
    utils.import_layers(file_path, layers, schema, prefix=prefix)
