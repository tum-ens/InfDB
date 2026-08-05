import os
import sys

from pyinfdb import InfDB

from . import utils

NAME = "dwd"


def load(infdb: InfDB) -> bool:
    """Downloads the DWD GeoPackage from the NEED cloud (WebDAV) and imports all its layers.

    Same pattern as waermeatlas_hessen_bensheim, but the layer list is discovered
    from the downloaded file instead of being configured, so every layer is imported.
    """
    file_path: str | None = None  # for safe logging if errors occur before assignment
    try:
        log = infdb.get_worker_logger()
        if not utils.if_active(NAME, infdb):
            return True

        cfg = [infdb.get_toolname(), "sources", NAME]

        base_path = infdb.get_config_path(cfg + ["path", "base"], type="loader")
        os.makedirs(base_path, exist_ok=True)

        url: str = infdb.get_config_value(cfg + ["url"])

        # Protocol (defaults to plain http if not configured)
        try:
            protocol = infdb.get_config_value(cfg + ["protocol"])
        except Exception:
            protocol = "http"

        # WebDAV credentials: username from config, token from the environment
        username = None
        access_token = None
        if protocol == "webdav":
            username = infdb.get_config_value(cfg + ["username"])
            access_token = infdb.get_env_variable("WEBDAV_NEED_INTERNAL_ACCESS_TOKEN")

        filename, *_ = utils.get_file_from_url(url)
        file_path = os.path.join(base_path, filename)

        log.info(f"Downloading {NAME} data from %s to %s", url, file_path)
        utils.download_files(url, base_path, infdb, protocol, username=username, access_token=access_token)

        schema: str = infdb.get_config_value(cfg + ["schema"])
        with infdb.connect() as db:
            db.execute_query(f"CREATE SCHEMA IF NOT EXISTS {schema};")

        prefix: str = infdb.get_config_value(cfg + ["prefix"]) or NAME

        # Import every layer found in the GeoPackage (we don't hardcode a layer list).
        layers = utils.get_gpkg_layers(file_path)
        if not layers:
            log.warning(f"{NAME}: no layers found in {file_path}; nothing to import.")
            return True
        log.info(f"{NAME}: found %d layers: %s", len(layers), ", ".join(layers))

        # Optional scope clipping (default True, like the other cloud loaders).
        # Set 'scope: false' in the config to import the data unclipped.
        try:
            scope_cfg = infdb.get_config_value(cfg + ["scope"])
        except Exception:
            scope_cfg = None
        scope = True if scope_cfg is None else bool(scope_cfg)

        log.info(f"Loading {NAME} data from %s to %s (scope clip: %s)", url, file_path, scope)
        utils.import_layers(file_path, layers, schema, infdb, prefix=prefix, scope=scope)

        log.info(f"{NAME} data loaded successfully")
        sys.exit(0)

    except Exception as err:
        log.exception(
            f"An error occurred while processing {NAME} file: %s %s",
            file_path if file_path else "<unknown>",
            str(err),
        )
        sys.exit(1)
