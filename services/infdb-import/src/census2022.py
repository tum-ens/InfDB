import multiprocessing as mp
import os
import sys
from typing import Any, Dict, Iterable, List

from infdb import InfDB

from . import utils

# ============================== Constants ==============================
CLIPPED_PREFIX: str = "zensus-2022"


def load(infdb: InfDB) -> None:
    """Entry point to download, validate, and process Zensus 2022 datasets.

    Behavior preserved:
    - Respects `utils.if_active("zensus_2022", infdb)`.
    - Validates page links vs YAML list and logs differences.
    - Creates schema if missing.
    - Spawns a process pool with a per-process logger initializer.
    """

    try:
        log = infdb.get_worker_logger()

        if not utils.if_active("zensus_2022", infdb):
            return

        datasets: List[Dict[str, Any]] = infdb.get_config_value(
            [infdb.get_toolname(), "sources", "zensus_2022", "datasets"]
        )

        url = infdb.get_config_value([infdb.get_toolname(), "sources", "zensus_2022", "url"])

        zip_links: List[str] = utils.get_website_links(url, infdb)

        # validate links
        yaml_links = {entry["url"] for entry in datasets}
        original_set = set(zip_links)
        missing_in_yaml = original_set - yaml_links
        extra_in_yaml = yaml_links - original_set
        if missing_in_yaml:
            log.warning("Links in original list but NOT in YAML:")
            for lnk in sorted(missing_in_yaml):
                log.warning(" - %s", lnk)
        if extra_in_yaml:
            log.warning("Links in YAML but NOT in original list:")
            for lnk in sorted(extra_in_yaml):
                log.warning(" - %s", lnk)

        # create schema (via package client)
        schema = infdb.get_config_value([infdb.get_toolname(), "sources", "zensus_2022", "schema"])
        with infdb.connect() as db:
            db.execute_query(f"CREATE SCHEMA IF NOT EXISTS {schema};")

        # folders
        zip_path = infdb.get_config_path(
            [infdb.get_toolname(), "sources", "zensus_2022", "path", "zip"],
            type="loader",
        )

        os.makedirs(zip_path, exist_ok=True)
        unzip_path = infdb.get_config_path(
            [infdb.get_toolname(), "sources", "zensus_2022", "path", "unzip"], type="loader"
        )
        os.makedirs(unzip_path, exist_ok=True)

        number_processes = utils.get_number_processes(infdb)
        with mp.Pool(
            processes=number_processes,
            # initializer=_init_logger_for_process,
            # initargs=(infdb,),
        ) as pool:
            results = pool.starmap(
                process_dataset,
                [
                    (
                        dataset,
                        infdb.get_toolname(),
                    )
                    for dataset in datasets
                ],
            )

        if not all(results):
            raise RuntimeError("Some datasets failed to process")
        else:
            sys.exit(0)
    except Exception as err:
        log.exception("An error occurred while processing Census: %s", str(err))
        sys.exit(1)


def process_dataset(dataset: Dict[str, Any], tool_name: str) -> bool:
    """Downloads, unzips, transforms, and loads one dataset to PostGIS.

    Args:
        dataset: A dataset record from config (`name`, `url`, `year`, `table_name`, `status`, ...).
        tool_name: The name of the tool (for logging/config).

    Returns:
        True on success or skip; False when an exception is encountered (logged).
    """
    try:
        # Initialize InfDB in each worker process
        infdb = InfDB(tool_name=tool_name, config_path="../configs/config-infdb-import.yml")
        log = infdb.get_worker_logger()

        log.info("Working on %s", dataset["name"])

        # status gate
        if dataset["status"] != "active":
            log.info("%s skips, status not active", dataset["name"])
            return True

        years: Iterable[int] = infdb.get_config_value([infdb.get_toolname(), "sources", "zensus_2022", "years"])
        if dataset["year"] not in years:
            log.info("%s skips, not in years list", dataset["name"])
            return True

        # Download INTO the zip directory and use the returned file path
        zip_dir = infdb.get_config_path([infdb.get_toolname(), "sources", "zensus_2022", "path", "zip"], type="loader")
        link = dataset["url"]
        downloaded = utils.download_files(link, zip_dir, infdb)  # returns [<zip_file_path>]
        zip_file = downloaded[0]

        # Unzip using the real file path
        unzip_dir = infdb.get_config_path(
            [infdb.get_toolname(), "sources", "zensus_2022", "path", "unzip"], type="loader"
        )
        folder_path = os.path.join(unzip_dir, dataset["table_name"])
        utils.unzip(zip_file, folder_path, infdb)
        # Export to PostGIS for each configured resolution
        resolutions: List[str] = infdb.get_config_value([infdb.get_toolname(), "sources", "zensus_2022", "resolutions"])

        prefix = infdb.get_config_value([infdb.get_toolname(), "sources", "zensus_2022", "prefix"])
        schema = infdb.get_config_value([infdb.get_toolname(), "sources", "zensus_2022", "schema"])
        epsg = (infdb.get_db_parameters_dict() or {}).get("epsg")  # target DB SRID

        # Export to PostGIS
        for resolution in resolutions:
            log.info("Processing %s with %s ...", dataset["name"], resolution)

            # Search for corresponding CSV within the unzipped folder
            csv_path = utils.get_file(folder_path, resolution, ".csv", infdb)
            if not csv_path:
                log.warning(f"No file for {dataset['name']} with resolution {resolution} found")
                continue

            # -------------------------
            # FAST LOAD (NEW): COPY + server-side geometry creation
            # This replaces: read CSV -> build GeoDataFrame -> gdf.to_postgis(...)
            # Benefits:
            #   * COPY is much faster than per-row inserts
            #   * ST_MakePoint + ST_Transform happen inside PostGIS (C), not Python
            # -------------------------
            x_col = f"x_mp_{resolution}"  # Zensus CSV columns for X/Y per resolution
            y_col = f"y_mp_{resolution}"
            table_name = f"{prefix}_{dataset['year']}_{resolution}_{dataset['table_name']}"

            # column types from config
            column_types = dataset.get("types", {}) or {}
            # normalize keys to lowercase (safe)
            column_types = {k.strip().lower(): v.strip().lower() for k, v in column_types.items()}

            utils.fast_copy_points_csv(
                infdb,
                csv_path=csv_path,
                schema=schema,
                table_name=table_name,
                x_col=x_col,
                y_col=y_col,
                srid_src=3035,  # source X/Y are in EPSG:3035 in the Zensus CSV
                epsg=epsg,  # target SRID from DB config
                drop_existing=True,  # matches old 'replace' behavior
                create_spatial_index=True,  # gives you good query perf right away
                clip_to_scope=True,  # Explicit clipping (default anyway)
                column_types=column_types,  # custom column types from config
            )

            log.info(f"Processed successfully {csv_path}")

        # if we reach here without exceptions, this dataset was processed OK
        return True

    except Exception as err:
        if "log" not in locals():
            print(f"Error in process_dataset({dataset.get('name')}): {err}")
        else:
            log.exception(
                "An error occurred while processing file: %s %s",
                dataset.get("name"),
                str(err),
            )
        return False
