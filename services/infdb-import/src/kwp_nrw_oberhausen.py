import os
import sys
from typing import List, Sequence

from infdb import InfDB

from . import utils

NAME = "kwp-nrw-oberhausen"


def load(infdb: InfDB) -> None:
    """Entry point to download, validate, and process KWP NRW datasets from heat atlas NRW.

    Behavior preserved:
    - Respects `utils.if_active("kwp-nrw-oberhausen", infdb)`.
    - Validates page links vs YAML list and logs differences.
    - Creates schema if missing.
    - Spawns a process pool with a per-process logger initializer.
    """
    file_path: str | None = None  # for safe logging if errors occur before assignment
    try:
        log = infdb.get_worker_logger()
        if not utils.if_active(NAME, infdb):
            return

        # create data folders if not existent
        # Zip path
        zip_path = infdb.get_config_path([infdb.get_toolname(), "sources", NAME, "path", "zip"], type="loader")
        log.debug("zip_path=%s", zip_path)
        os.makedirs(zip_path, exist_ok=True)
        # Unzip path
        unzip_path = infdb.get_config_path([infdb.get_toolname(), "sources", NAME, "path", "unzip"], type="loader")
        log.debug("unzip_path=%s", unzip_path)
        os.makedirs(unzip_path, exist_ok=True)

        url: str = infdb.get_config_value([infdb.get_toolname(), "sources", NAME, "url"])
        log.debug("url=%s", url)

        filename, *_ = utils.get_file_from_url(url)

        # Download INTO the zip directory and use the returned file path
        zip_file = os.path.join(zip_path, filename)
        log.debug(f"Downloading {NAME} data from %s to %s", url, zip_file)
        utils.download_files(url, zip_path, infdb)

        # Unzip using the real file path
        unzip_dir = infdb.get_config_path([infdb.get_toolname(), "sources", NAME, "path", "unzip"], type="loader")
        utils.unzip(zip_file, unzip_dir, infdb)
        file_path = os.path.join(unzip_dir, filename.replace(".zip", ""))

        schema: str = infdb.get_config_value([infdb.get_toolname(), "sources", NAME, "schema"])
        # Ensure schema exists using InfdbClient
        with infdb.connect() as db:
            db.execute_query(f"CREATE SCHEMA IF NOT EXISTS {schema};")

        prefix: str = infdb.get_config_value([infdb.get_toolname(), "sources", NAME, "prefix"])
        layers: Sequence[str] = infdb.get_config_value([infdb.get_toolname(), "sources", NAME, "layer"])

        shp_files: List[str] = utils.get_all_files(unzip_dir, ending=".shp")
        for layer in layers:
            # Find the .shp file in shp_files where layer is a substring
            file_path = next((shp for shp in shp_files if layer in shp), None)
            if file_path is None:
                log.warning(f"No .shp file found for layer '{layer}' in {shp_files}")
                continue
            log.info(f"Loading {NAME} data from %s to postGIS", file_path)
            layer_str = os.path.splitext(os.path.basename(file_path))[0]  # get layer name = file name without extension
            utils.import_layers(file_path, [layer_str], schema, infdb, prefix=prefix, layer_names=[layer], scope=True)

        log.info(f"{NAME} data loaded successfully")
        sys.exit(0)

    except Exception as err:
        log.exception("An error occurred while processing KWP-NRW-Oberhausen: %s", str(err))
        sys.exit(1)
