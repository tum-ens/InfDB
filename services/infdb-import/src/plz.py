import os
import shutil
import sys
import time
from typing import Sequence
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from pyinfdb import InfDB

from . import utils


def _is_feature_collection(file_path: str) -> bool:
    """True if the file looks like a complete GeoJSON FeatureCollection (not an ArcGIS status message).

    A heuristic on the start and the end only: the file is ~200 MB, too large to parse just for this
    check. ArcGIS Hub exports end with the closing feature list (`]}`), so a download cut off in the
    middle is rejected; corrupted content inside the file is not detected.
    """
    with open(file_path, "rb") as f:
        head = f.read(512)
        f.seek(max(0, os.path.getsize(file_path) - 64))
        tail = b"".join(f.read().split())  # ignore JSON whitespace, e.g. "]\n}" in pretty-printed files
    return head.lstrip().startswith(b"{") and b'"FeatureCollection"' in head and tail.endswith(b"]}")


def _download_file(url: str, file_path: str, log, attempts: int = 20, wait_seconds: int = 30) -> None:
    """Downloads to a temporary file and keeps it only if it is a GeoJSON FeatureCollection.

    While ArcGIS Hub regenerates an export it answers with a small JSON status
    ("status": "Pending") instead of data; saving that would poison the cache.
    """
    if urlparse(url).scheme not in ("http", "https"):
        raise ValueError("PLZ download requires HTTP or HTTPS")
    tmp_path = f"{file_path}.part"
    for attempt in range(1, attempts + 1):
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        # URL scheme validated above, custom/local protocols rejected.
        with urlopen(request, timeout=60) as response, open(tmp_path, "wb") as out_file:  # nosec B310
            shutil.copyfileobj(response, out_file)
        if _is_feature_collection(tmp_path):
            os.replace(tmp_path, file_path)
            return
        log.warning("No GeoJSON yet from %s (attempt %d/%d), retrying in %ds", url, attempt, attempts, wait_seconds)
        time.sleep(wait_seconds)
    os.remove(tmp_path)
    raise RuntimeError(f"No GeoJSON FeatureCollection from {url} after {attempts} attempts")


def _ensure_consumer_columns(infdb: InfDB, schema: str, table: str) -> None:
    """Keeps the columns downstream tools select (e.g. PyLovo: plz, note, qkm, einwohner, geom).

    ArcGIS layer 4 names the postcode `postal_code` and has no `einwohner`, `qkm` or `note`;
    these columns are created empty so existing queries keep working.
    """
    with infdb.connect() as db:
        db.execute_query(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.columns
                           WHERE table_schema = '{schema}' AND table_name = '{table}' AND column_name = 'postal_code')
                   AND NOT EXISTS (SELECT 1 FROM information_schema.columns
                           WHERE table_schema = '{schema}' AND table_name = '{table}' AND column_name = 'plz') THEN
                    ALTER TABLE {schema}.{table} RENAME COLUMN postal_code TO plz;
                END IF;
            END $$;
            ALTER TABLE {schema}.{table}
                ADD COLUMN IF NOT EXISTS einwohner integer,
                ADD COLUMN IF NOT EXISTS qkm double precision,
                ADD COLUMN IF NOT EXISTS note varchar;
        """)


def load(infdb: InfDB) -> bool:
    """Downloads PLZ dataset from ArcGIS Hub, ensures schema, and imports configured layers.

    Behavior preserved:
    - Early exit (True) when feature flag `plz` is inactive.
    - Skips download when a valid GeoJSON file already exists (a cached status message is re-downloaded).
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

        if os.path.exists(file_path) and _is_feature_collection(file_path):
            log.info("File %s already exists.", file_path)
        else:
            log.info("File %s will be downloaded from %s", file_path, url)
            _download_file(url, file_path, log)

        schema: str = infdb.get_config_value([infdb.get_toolname(), "sources", "plz", "schema"])

        with infdb.connect() as db:
            db.execute_query(f"CREATE SCHEMA IF NOT EXISTS {schema};")

        prefix: str = infdb.get_config_value([infdb.get_toolname(), "sources", "plz", "prefix"])
        layers: Sequence[str] = infdb.get_config_value([infdb.get_toolname(), "sources", "plz", "layer"])

        log.info("Loading PLZ data from %s to %s", url, file_path)
        utils.import_layers(file_path, layers, schema, infdb, prefix=prefix, layer_names=["germany"])
        # Same table name as import_layers; GDAL lower-cases table names
        table = (f"{prefix}_germany" if prefix else "germany").lower()
        _ensure_consumer_columns(infdb, schema, table)

        log.info("PLZ data loaded successfully")
        sys.exit(0)

    except Exception as err:
        log.exception(
            "An error occurred while processing plz file: %s %s",
            file_path if file_path else "<unknown>",
            str(err),
        )
        sys.exit(1)
