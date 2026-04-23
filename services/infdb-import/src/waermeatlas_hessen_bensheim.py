import os
import sys
from typing import Sequence

from infdb import InfDB

from . import utils

NAME = "waermeatlas-hessen-bensheim"


def load(infdb: InfDB) -> bool:
    """Downloads Gebäude neuburg dataset (if active), ensures schema, and imports configured layers.

    Behavior preserved:
    - Early exit (True) when feature flag `gebaeude-neuburg` is inactive.
    - Skips download when the target file already exists.
    - Ensures schema via InfdbClient and imports layers with configured prefix.
    """
    file_path: str | None = None  # for safe logging if errors occur before assignment
    try:
        log = infdb.get_worker_logger()
        if not utils.if_active(NAME, infdb):
            return True

        base_path = infdb.get_config_path([infdb.get_toolname(), "sources", NAME, "path", "base"], type="loader")
        log.debug("base_path=%s", base_path)
        os.makedirs(base_path, exist_ok=True)

        url: str = infdb.get_config_value([infdb.get_toolname(), "sources", NAME, "url"])
        log.debug("url=%s", url)

        # Get auth flag (defaults to False if not present)
        try:
            protocol = infdb.get_config_value([infdb.get_toolname(), "sources", NAME, "protocol"])
        except Exception:
            protocol = "http"

        # Get credentials if auth is enabled
        username = None
        access_token = None
        if protocol == "webdav":
            username = infdb.get_config_value([infdb.get_toolname(), "sources", NAME, "username"])
            access_token = infdb.get_env_variable("WEBDAV_NEED_INTERNAL_ACCESS_TOKEN")

        filename, *_ = utils.get_file_from_url(url)

        file_path = os.path.join(base_path, filename)
        log.debug(f"Downloading {NAME} data from %s to %s", url, file_path)

        utils.download_files(url, base_path, infdb, protocol, username=username, access_token=access_token)

        schema: str = infdb.get_config_value([infdb.get_toolname(), "sources", NAME, "schema"])

        # Ensure schema exists using InfdbClient
        with infdb.connect() as db:
            db.execute_query(f"CREATE SCHEMA IF NOT EXISTS {schema};")

        prefix: str = infdb.get_config_value([infdb.get_toolname(), "sources", NAME, "prefix"])
        layers: Sequence[str] = infdb.get_config_value([infdb.get_toolname(), "sources", NAME, "layer"])

        log.info(f"Loading {NAME} data from %s to %s", url, file_path)
        utils.import_layers(file_path, layers, schema, infdb, prefix=prefix)

        log.info(f"{NAME} data loaded successfully")
        sys.exit(0)

    except Exception as err:
        log.exception(
            f"An error occurred while processing {NAME} file: %s %s",
            file_path if file_path else "<unknown>",
            str(err),
        )
        sys.exit(1)
