import os
import sys
from typing import List, Sequence

from infdb import InfDB

from . import utils


def load(infdb: InfDB) -> None:
    """Downloads and imports basemap data based on configuration."""
    log = infdb.get_worker_logger()
    try:
        if not utils.if_active("basemap", infdb):
            log.info("Basemap loader inactive → skipping.")
            return
        base_path = infdb.get_config_path([infdb.get_toolname(), "sources", "basemap", "path", "base"], type="loader")
        os.makedirs(base_path, exist_ok=True)

        site_url = infdb.get_config_value([infdb.get_toolname(), "sources", "basemap", "url"])
        ending = infdb.get_config_value([infdb.get_toolname(), "sources", "basemap", "ending"])
        filters: Sequence[str] = infdb.get_config_value([infdb.get_toolname(), "sources", "basemap", "filter"]) or []

        schema = infdb.get_config_value([infdb.get_toolname(), "sources", "basemap", "schema"])
        prefix = infdb.get_config_value([infdb.get_toolname(), "sources", "basemap", "prefix"])
        layer_names: Sequence[str] = infdb.get_config_value([infdb.get_toolname(), "sources", "basemap", "layer"]) or []

        # make sure schema exists
        with infdb.connect() as db:
            # db.execute_query(f"DROP SCHEMA IF EXISTS {schema} CASCADE;") # done in main.py
            db.execute_query(f"CREATE SCHEMA IF NOT EXISTS {schema};")

        for flt in filters:
            urls: List[str] = utils.get_links(site_url, ending, flt, infdb)
            if len(urls) != 1:
                log.warning("Basemap: filter '%s' produced %d links → %s (skipping)", flt, len(urls), urls)
                continue
            else:
                url = urls[0]
            log.info("Basemap: selected %s for filter '%s'", url, flt)

            filename, name, extension = utils.get_file_from_url(url)
            name_no_day = name.rsplit("-", 1)[0]
            expected_monthly_path = os.path.join(base_path, name_no_day + extension)

            log.info("Basemap: downloading to path %s", expected_monthly_path)
            utils.download_files(url, expected_monthly_path, infdb)

            download_file = utils.get_file(base_path, flt, ".gpkg", infdb)

            log.info("Basemap: importing %s into schema %s", download_file, schema)
            layers = [layer + "_bdlm" for layer in layer_names]
            utils.import_layers(
                download_file, layers, schema, infdb, prefix=prefix, layer_names=layer_names, overwrite=False
            )

        with infdb.connect() as db:
            log.info("Creating index on id column for %s.%s_verkehrslinie", schema, prefix)
            ddl = f"""
                CREATE INDEX IF NOT EXISTS {prefix}_verkehrslinie_id_idx
                ON {schema}.{prefix}_verkehrslinie (id);
            """
            db.execute_query(ddl)

        log.info("Basemap data loaded successfully")
        sys.exit(0)
    except Exception as err:
        log.exception("An error occurred while processing BASEMAP data: %s", str(err))
        sys.exit(1)
