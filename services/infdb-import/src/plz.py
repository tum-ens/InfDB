import os
import sys
import shutil
from typing import Sequence
from urllib.request import Request, urlopen

from infdb import InfDB

from . import utils


def _download_file(url: str, file_path: str) -> None:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request) as response, open(file_path, "wb") as out_file:
        shutil.copyfileobj(response, out_file)


def load(infdb: InfDB) -> bool:
    """Downloads PLZ dataset from ArcGIS Hub, ensures schema, and imports configured layers.

    Behavior preserved:
    - Early exit (True) when feature flag `plz` is inactive.
    - Skips download when the target file already exists.
    - Ensures schema via InfdbClient and imports layers with configured prefix.
    """
    file_path: str | None = None
    try:
        log = infdb.get_worker_logger()
        if not utils.if_active("plz", infdb):
            return True

        base_path = infdb.get_config_path([infdb.get_toolname(), "sources", "plz", "path", "base"], type="loader")
        log.debug("base_path=%s", base_path)
        os.makedirs(base_path, exist_ok=True)

        url: str = infdb.get_config_value([infdb.get_toolname(), "sources", "plz", "url"])
        filename: str = infdb.get_config_value([infdb.get_toolname(), "sources", "plz", "filename"])

        file_path = os.path.join(base_path, filename)
        log.debug("Downloading PLZ data from %s to %s", url, file_path)

        if os.path.exists(file_path):
            log.info("File %s already exists.", file_path)
        else:
            log.info("File %s will be downloaded from %s", file_path, url)
            _download_file(url, file_path)

        schema: str = infdb.get_config_value([infdb.get_toolname(), "sources", "plz", "schema"])

        with infdb.connect() as db:
            db.execute_query(f"CREATE SCHEMA IF NOT EXISTS {schema};")

        prefix: str = infdb.get_config_value([infdb.get_toolname(), "sources", "plz", "prefix"])
        layers: Sequence[str] = infdb.get_config_value([infdb.get_toolname(), "sources", "plz", "layer"])

        log.info("Loading PLZ data from %s to %s", url, file_path)
        utils.import_layers(file_path, layers, schema, infdb, prefix=prefix, layer_names=["germany"])

        log.info("PLZ data loaded successfully")
        sys.exit(0)

    except Exception as err:
        log.exception(
            "An error occurred while processing plz file: %s %s",
            file_path if file_path else "<unknown>",
            str(err),
        )
        sys.exit(1)