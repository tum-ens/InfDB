import multiprocessing as mp
import os
import sys
from typing import Any, Dict, List

from infdb import InfDB

from . import utils


def load(infdb: InfDB) -> None:
    """Entry point to download, validate, and process KWP NRW datasets from heat atlas NRW.

    Behavior preserved:
    - Respects `utils.if_active("kwp-nrw", infdb)`.
    - Validates page links vs YAML list and logs differences.
    - Creates schema if missing.
    - Spawns a process pool with a per-process logger initializer.
    """

    try:
        log = infdb.get_worker_logger()

        if not utils.if_active("kwp-nrw", infdb):
            return

        datasets: List[Dict[str, Any]] = infdb.get_config_value(
            [infdb.get_toolname(), "sources", "kwp-nrw", "datasets"]
        )

        # create schema (via package client)
        schema = infdb.get_config_value([infdb.get_toolname(), "sources", "kwp-nrw", "schema"])
        prefix = infdb.get_config_value([infdb.get_toolname(), "sources", "kwp-nrw", "prefix"])
        with infdb.connect() as db:
            db.execute_query(f"CREATE SCHEMA IF NOT EXISTS {schema};")

        # folders
        zip_path = infdb.get_config_path([infdb.get_toolname(), "sources", "kwp-nrw", "path", "zip"], type="loader")
        os.makedirs(zip_path, exist_ok=True)
        unzip_path = infdb.get_config_path([infdb.get_toolname(), "sources", "kwp-nrw", "path", "unzip"], type="loader")
        os.makedirs(unzip_path, exist_ok=True)

        number_processes = utils.get_number_processes(infdb)
        with mp.Pool(
            processes=number_processes,
            # initializer=_init_logger_for_process,
            # initargs=(infdb,),
        ) as pool:
            results = pool.starmap(
                process_dataset, [(dataset, infdb.get_toolname(), schema, prefix) for dataset in datasets]
            )

        if not all(results):
            raise RuntimeError("Some datasets failed to process")
        else:
            sys.exit(0)
    except Exception as err:
        log.exception("An error occurred while processing KWP-NRW: %s", str(err))
        sys.exit(1)


def process_dataset(dataset: Dict[str, Any], tool_name: str, schema: str, prefix: str) -> bool:
    """Downloads, unzips, transforms, and loads one dataset to PostGIS.

    Args:
        dataset: A dataset record from config (`name`, `url`, `year`, `table_name`, `status`, ...).
        tool_name: The name of the tool (for logging/config).
        schema: Target database schema.
        prefix: Prefix for table names.

    Returns:
        True on success or skip; False when an exception is encountered (logged).
    """
    try:
        # Initialize InfDB in each worker process
        infdb = InfDB(tool_name=tool_name)
        log = infdb.get_worker_logger()

        log.info("Working on %s", dataset["name"])

        # status gate
        if dataset["status"] != "active":
            log.info("%s skips, status not active", dataset["name"])
            return True

        # # Download INTO the zip directory and use the returned file path
        zip_dir = infdb.get_config_path([infdb.get_toolname(), "sources", "kwp-nrw", "path", "zip"], type="loader")
        link = dataset["url"]
        downloaded = utils.download_files(link, zip_dir, infdb)  # returns [<zip_file_path>]
        zip_file = downloaded[0]

        # Unzip using the real file path
        unzip_dir = infdb.get_config_path([infdb.get_toolname(), "sources", "kwp-nrw", "path", "unzip"], type="loader")
        folder_path = os.path.join(unzip_dir, dataset["table_name"])
        utils.unzip(zip_file, folder_path, infdb)

        # layers
        layers = dataset.get("layer", [])

        if len(layers) > 1:
            layer_names = [
                f"{dataset['table_name']}_{layer}".replace("_Energietraeger_OpenData", "") for layer in layers
            ]
        else:
            layer_names = [f"{dataset['table_name']}".replace("_Energietraeger_OpenData", "") for layer in layers]

        # Export to PostGIS
        log.info("Processing %s", dataset["name"])

        gdb = utils.get_subdirectories_by_suffix(folder_path, suffix=".gdb")[0]  # we expect exactly one .gdb folder

        utils.import_layers(gdb, layers, schema, infdb, prefix, layer_names)

        log.info("Processed sucessfully %s", gdb)
        return True
    except Exception as err:
        log.exception("An error occurred while processing: %s %s", dataset.get("name"), str(err))
        return False
