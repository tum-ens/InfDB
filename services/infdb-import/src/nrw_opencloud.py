import os
import sys
from typing import Sequence

from infdb import InfDB

from . import utils


def load(infdb: InfDB) -> bool:
    """Downloads Wärmebedarf datasets for NRW from opencloud (if active), ensures schema, and imports configured layers.

    Behavior preserved:
    - Early exit (True) when feature flag `nrw-opencloud` is inactive.
    - Skips download when the target file already exists.
    - Ensures schema via InfdbClient and imports layers with configured prefix.
    """
    file_path: str | None = None  # for safe logging if errors occur before assignment
    try:
        log = infdb.get_worker_logger()
        if not utils.if_active("nrw-opencloud", infdb):
            return True

        base_path = infdb.get_config_path(
            [infdb.get_toolname(), "sources", "nrw-opencloud", "path", "base"], type="loader"
        )
        log.debug("base_path=%s", base_path)
        os.makedirs(base_path, exist_ok=True)

        url: str = infdb.get_config_value([infdb.get_toolname(), "sources", "nrw-opencloud", "url"])
        log.debug("url=%s", url)

        # Get auth flag (defaults to False if not present)
        try:
            protocol = infdb.get_config_value([infdb.get_toolname(), "sources", "nrw-opencloud", "protocol"])
        except Exception:
            protocol = "http"

        # Get credentials if auth is enabled
        # username = None
        # access_token = None
        # if protocol == "webdav":
        #     username = infdb.get_config_value([infdb.get_toolname(), "sources", "nrw-opencloud", "username"])
        #     access_token = infdb.get_config_value([infdb.get_toolname(), "sources", "nrw-opencloud","WEBDAV_NEED_INTERNAL_ACCESS_TOKEN"])
            

        filename, *_ = utils.get_file_from_url(url)

        file_path = os.path.join(base_path, filename)
        log.debug("Downloading NRW Wärmebedatf data from %s to %s", url, file_path)

        utils.download_files(url, base_path, infdb, protocol, username=None, access_token=None)

        schema: str = infdb.get_config_value([infdb.get_toolname(), "sources", "nrw-opencloud", "schema"])

        # Ensure schema exists using InfdbClient
        with infdb.connect() as db:
            db.execute_query(f"CREATE SCHEMA IF NOT EXISTS {schema};")

        prefix: str = infdb.get_config_value([infdb.get_toolname(), "sources", "nrw-opencloud", "prefix"])
        layers: Sequence[str] = infdb.get_config_value([infdb.get_toolname(), "sources", "nrw-opencloud", "layer"])

        log.info("Loading nrw-opencloud data from %s to %s", url, file_path)
        utils.import_layers(file_path, layers, schema, infdb, prefix=prefix)

        log.info("nrw-opencloud data loaded successfully")
        sys.exit(0)

    except Exception as err:
        log.exception(
            "An error occurred while processing nrw-opencloud files: %s %s",
            file_path if file_path else "<unknown>",
            str(err),
        )
        sys.exit(1)
