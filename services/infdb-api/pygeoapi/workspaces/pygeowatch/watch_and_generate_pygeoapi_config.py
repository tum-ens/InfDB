import logging
import pathlib
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import psycopg
import yaml
from infdb import InfDB
# from infdb.utils import atomic_write_yaml, build_dsn_from_env, read_env
import utils # import atomic_write_yaml, build_dsn_from_env, read_env
from psycopg import sql
from psycopg.rows import dict_row

# =========================
# ===== Module Constants ===
# =========================
infdb = InfDB(tool_name="infdb-pygeoapi", config_path="config-infdb-pygeoapi.yml")
OUTPUT_CONFIG_PATH: pathlib.Path = pathlib.Path("/workspaces/pygeoapi/pygeoapi-config.yml")
LOGGER_NAME: str = "pygeoapi_config_gen"

CRS84_URI: str = "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
GERMANY_BBOX_CRS84: List[float] = [5.866315, 47.270111, 15.041932, 55.058384]


# =========================
# ========= Logging ========
# =========================


def _setup_logging() -> logging.Logger:
    """Configures and returns the module logger.

    Reads LOG_LEVEL from environment (default: INFO), sets a simple log format,
    and returns a logger named by LOGGER_NAME.

    Returns:
        Configured logger instance.
    """
    level = (utils.read_env("LOG_LEVEL", "INFO") or "INFO").upper()
    level_num = getattr(logging, level, logging.INFO)
    logging.basicConfig(level=level_num, format="%(asctime)s %(levelname)s %(message)s")
    return logging.getLogger(LOGGER_NAME)


log = infdb.get_worker_logger()


# ---------- derived configuration constants (centralized env reads) ----------
PYGEOAPI_PORT_STRING: str = str(utils.read_env("SERVICES_PYGEOAPI_PORT", required=True))
if PYGEOAPI_PORT_STRING is None:
    raise ValueError("SERVICES_PYGEOAPI_PORT is required but not provided.")
PYGEOAPI_PORT: int = int(PYGEOAPI_PORT_STRING)
PYGEOAPI_HOST: str = utils.read_env("SERVICES_PYGEOAPI_BASE_HOST")
if PYGEOAPI_HOST is None:
    raise ValueError("SERVICES_PYGEOAPI_BASE_HOST is required but not provided.")

POSTGRES_USER: str = str(utils.read_env("SERVICES_POSTGRES_USER", required=True))
POSTGRES_PASSWORD: str = str(utils.read_env("SERVICES_POSTGRES_PASSWORD", required=True))
POSTGRES_DB: str = str(utils.read_env("SERVICES_POSTGRES_DB", required=True))
POSTGRES_HOST: str = str(utils.read_env("SERVICES_POSTGRES_HOST", required=True))
POSTGRES_PORT_STRING: str = str(utils.read_env("SERVICES_POSTGRES_EXPOSED_PORT", required=True))
if POSTGRES_PORT_STRING is None:
    raise ValueError("SERVICES_POSTGRES_EXPOSED_PORT is required but not provided.")
POSTGRES_PORT: int = int(POSTGRES_PORT_STRING)

TARGET_EPSG_STRING: str = str(utils.read_env("SERVICES_POSTGRES_EPSG", required=True))
if TARGET_EPSG_STRING is None:
    raise ValueError("SERVICES_POSTGRES_EPSG is required but not provided.")
TARGET_EPSG: int = int(TARGET_EPSG_STRING)

FALLBACK_EPSG: int = 25832

FORCE_CRS84_ONLY: bool = str(utils.read_env("SERVICES_PYGEOAPI_FORCE_CRS84_ONLY", "false")).lower() in (
    "1",
    "true",
    "yes",
    "y",
)

FORCE_DB_TRANSFORM_TABLES_RAW: str = utils.read_env("FORCE_DB_TRANSFORM_TABLES", "*") or "*"
_RAW_ITEMS: List[str] = [t.strip() for t in FORCE_DB_TRANSFORM_TABLES_RAW.split(",") if t.strip()]
_EXCLUDES: set[str] = {t[1:] for t in _RAW_ITEMS if t.startswith("!")}
_FORCE_SET: set[str] = {t for t in _RAW_ITEMS if not t.startswith("!")}
FORCE_DB_TRANSFORM_ALL: bool = ("*" in _FORCE_SET) or ("ALL" in _FORCE_SET)


def make_epsg_uri(epsg: int) -> str:
    """Returns the OGC EPSG URI for an EPSG code.

    Args:
        epsg: EPSG code as integer.

    Returns:
        OGC EPSG URI string for the given code.
    """
    return f"http://www.opengis.net/def/crs/EPSG/0/{int(epsg)}"


# Build DSN using shared package helper (keeps behavior but centralizes env parsing)
DB_DSN: str = utils.build_dsn_from_env(
    user_var=POSTGRES_USER,
    pwd_var=POSTGRES_PASSWORD,
    db_var=POSTGRES_DB,
    host_var=POSTGRES_HOST,
    port_var=POSTGRES_PORT,
)


# =========================
# ======= IO helpers ======
# =========================

def atomic_write_yaml(data: Any, output_path: str, file_mode: str | None = None, dir_mode: str | None = None) -> str:
    """
    Atomically serializes a Python object to YAML and writes to a file.

    Args:
        data: Python object to serialize to YAML (e.g., dict, list).
        output_path: Destination file path (absolute or relative). Parent directories
            will be created if needed.
        file_mode: Optional file permission mode (octal string, e.g. `"644"` or `"600"`).
        dir_mode: Optional directory permission mode (octal string) to apply to the
            destination directory.

    Returns:
        The absolute path of the written YAML file.

    Raises:
        ValueError: If `output_path` is empty.
        yaml.YAMLError: If the object cannot be serialized to YAML.
        OSError: If writing, syncing, or replacing the file fails (and potentially
            if applying `file_mode` fails).
    """
    yaml_text = yaml.safe_dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return utils.atomic_write_text(yaml_text, output_path, file_mode=file_mode, dir_mode=dir_mode)


class NoAliasDumper(yaml.SafeDumper):
    """YAML dumper that disables anchors/aliases."""

    def ignore_aliases(self, data: Any) -> bool:
        """Disables YAML anchors/aliases to keep output stable.

        Args:
            data: Any Python object.

        Returns:
            Always True to prevent YAML anchors/aliases.
        """
        return True


# ===============================
# ====== Change detection =======
# ===============================


def get_schema_signature(connection: psycopg.Connection[Any]) -> str:
    """Returns a stable signature of geometry-bearing columns in the DB.

    Args:
        connection: psycopg connection.

    Returns:
        Concatenated signature string (empty string if none) including
        schema.table.geom_col:srid for each geometry/geography column.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH geomcols AS (
              SELECT
                n.nspname   AS schema_name,
                c.relname   AS table_name,
                a.attname   AS geom_col,
                COALESCE(gc.srid, gg.srid) AS srid
              FROM pg_attribute a
              JOIN pg_class c ON c.oid = a.attrelid
              JOIN pg_namespace n ON n.oid = c.relnamespace
              JOIN pg_type t ON t.oid = a.atttypid
              LEFT JOIN public.geometry_columns gc
                ON gc.f_table_schema=n.nspname AND gc.f_table_name=c.relname AND gc.f_geometry_column=a.attname
              LEFT JOIN public.geography_columns gg
                ON gg.f_table_schema=n.nspname AND gg.f_table_name=c.relname AND gg.f_geography_column=a.attname
              WHERE a.attnum>0 AND NOT a.attisdropped
                AND c.relkind IN ('r','v','m','f','p')
                AND n.nspname NOT IN ('pg_catalog','information_schema','pg_toast')
                AND t.typname IN ('geometry','geography')
            )
            SELECT COALESCE(
              string_agg(schema_name||'.'||table_name||'.'||geom_col||':'||COALESCE(srid::text,''),'|' 
                ORDER BY schema_name,table_name,geom_col),''
            ) AS sig
            FROM geomcols;
            """
        )
        row = cursor.fetchone()
        result = (row or {}).get("sig") or ""
        log.debug("Finished get_schema_signature().")
        return result


def get_dml_signature_geom(connection: psycopg.Connection[Any]) -> int:
    """Returns a monotonic-ish DML counter across geometry-bearing tables.

    Args:
        connection: psycopg connection.

    Returns:
        Sum of insert/update/delete/hot_update counters across user tables
        that contain geometry/geography columns.
    """
    log.debug("Executing get_dml_signature_geom() ...")
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COALESCE(SUM(s.n_tup_ins + s.n_tup_upd + s.n_tup_del + s.n_tup_hot_upd), 0) AS dml_sum
            FROM pg_stat_user_tables s
            JOIN pg_class c ON c.oid = s.relid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname NOT IN ('pg_catalog','information_schema','pg_toast')
              AND EXISTS (
                SELECT 1 FROM pg_attribute a
                JOIN pg_type t ON t.oid=a.atttypid
                WHERE a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped AND t.typname IN ('geometry','geography')
              );
            """
        )
        row = cursor.fetchone()
        result = int((row or {}).get("dml_sum") or 0)
        log.debug("Finished get_dml_signature_geom().")
        return result


# =========================
# ======= DB helpers ======
# =========================


def list_columns(cursor: psycopg.Cursor[Any], schema: str, table: str) -> List[Tuple[str, str]]:
    """Lists column names and types for a table.

    Args:
        cursor: psycopg cursor.
        schema: Schema name.
        table: Table name.

    Returns:
        List of (column_name, udt_name) tuples ordered by ordinal position.
    """
    cursor.execute(
        """
        SELECT column_name, udt_name
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """,
        (schema, table),
    )
    result = [(r["column_name"], r["udt_name"]) for r in cursor.fetchall()]
    log.debug("Finished list_columns().")
    return result


def list_geometry_sources(cursor) -> list[dict]:
    """Enumerates geometry/geography sources in the DB.

    Uses geometry_columns/geography_columns if available; falls back to catalogs.
    Avoids reserved-word issues by not using `table` as a SQL column alias and
    mapping it back to the expected Python key ('table') in the result dicts.
    """
    log.debug("Executing list_geometry_sources() ...")
    sources: list[dict] = []

    def has_view(view_schema: str, view_name: str) -> bool:
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
            LIMIT 1
            """,
            (view_schema, view_name),
        )
        return cursor.fetchone() is not None

    # Prefer public/topology.geometry_columns if present
    has_geometry_view = has_view("public", "geometry_columns") or has_view("topology", "geometry_columns")
    if has_geometry_view:
        try:
            cursor.execute(
                """
                SELECT
                  f_table_schema AS schema,
                  f_table_name   AS table_name,       -- avoid reserved keyword in SQL
                  f_geometry_column AS geom_col,
                  srid,
                  type AS geom_type
                FROM public.geometry_columns
                ORDER BY 1,2,3
                """
            )
            for row in cursor.fetchall():
                sources.append(
                    {
                        "schema": row["schema"],
                        "table": row["table_name"],  # map back to expected key
                        "geom_col": row["geom_col"],
                        "srid": row["srid"],
                        "geom_type": row["geom_type"],
                        "is_geography": False,
                    }
                )
        except Exception as ex:
            log.info("Failed list_geometry_sources in case has_geometry_view with exception: ", ex)

    # geography_columns if present
    has_geog_view = has_view("public", "geography_columns")
    if has_geog_view:
        try:
            cursor.execute(
                """
                SELECT
                  f_table_schema   AS schema,
                  f_table_name     AS table_name,     -- avoid reserved keyword in SQL
                  f_geography_column AS geom_col,
                  srid,
                  type AS geom_type
                FROM public.geography_columns
                ORDER BY 1,2,3
                """
            )
            for row in cursor.fetchall():
                sources.append(
                    {
                        "schema": row["schema"],
                        "table": row["table_name"],  # map back to expected key
                        "geom_col": row["geom_col"],
                        "srid": row["srid"],
                        "geom_type": row["geom_type"],
                        "is_geography": True,
                    }
                )
        except Exception as ex:
            log.info("Failed list_geometry_sources in case has_geog_view with exception: ", ex)

    if sources:
        log.debug("Finished list_geometry_sources(), sources not empty.")
        return sources
    log.debug("sources is empty, compute sources with fallback case.")

    # Fallback: catalog introspection (avoid reserved word in SQL; map in Python)
    cursor.execute(
        """
        WITH cols AS (
          SELECT
            n.nspname   AS schema,
            c.relname   AS relname,     -- do not call it "table" in SQL
            a.attname   AS geom_col,
            t.typname   AS typname
          FROM pg_attribute a
          JOIN pg_class c      ON c.oid = a.attrelid
          JOIN pg_namespace n  ON n.oid = c.relnamespace
          JOIN pg_type t       ON t.oid = a.atttypid
          WHERE a.attnum > 0
            AND NOT a.attisdropped
            AND c.relkind IN ('r','v','m','f','p')
            AND n.nspname NOT IN ('pg_catalog','information_schema','pg_toast')
            AND t.typname IN ('geometry','geography')
        )
        SELECT schema, relname, geom_col, typname
        FROM cols
        ORDER BY 1,2,3
        """
    )
    for row in cursor.fetchall():
        sources.append(
            {
                "schema": row["schema"],
                "table": row["relname"],  # map to expected key
                "geom_col": row["geom_col"],
                "srid": None,
                "geom_type": None,
                "is_geography": (row["typname"] == "geography"),
            }
        )

    log.debug("Finished list_geometry_sources().")
    return sources


def pick_id_column(cursor: psycopg.Cursor[Any], schema: str, table: str) -> Optional[str]:
    """Picks the first column containing 'id' (case-insensitive).

    Args:
        cursor: psycopg cursor.
        schema: Schema name.
        table: Table name.

    Returns:
        Identifier column name, or None if not found.
    """
    cols = list_columns(cursor, schema, table)
    for name, _typ in cols:
        if "id" in name.lower():
            return name
    return None


# =============================
# ===== SRID resolution =======
# =============================


def resolve_srid(
    cursor: psycopg.Cursor[Any],
    schema: str,
    table: str,
    geometry_column: str,
    srid_hint: Optional[int],
) -> int:
    """Resolves SRID using hint, sampling, or fallback (env only, no overrides).

    Tries, in order:
      1) The provided `srid_hint` if present and > 0 (from geometry_columns or similar),
      2) Sample the table for the first non-null geometry's ST_SRID,
      3) Fall back to FALLBACK_EPSG (from environment).

    Args:
        cursor: psycopg cursor.
        schema: Schema name.
        table: Table name.
        geometry_column: Geometry column name.
        srid_hint: Optional SRID hint (may be None).

    Returns:
        Determined SRID (EPSG code). Falls back to FALLBACK_EPSG.
    """
    if isinstance(srid_hint, int) and srid_hint > 0:
        return int(srid_hint)

    log.debug("Executing resolve_srid() ...")
    try:
        query = sql.SQL(
            """
            SELECT ST_SRID({geom}) AS srid
            FROM {schema}.{table}
            WHERE {geom} IS NOT NULL
            LIMIT 1
            """
        ).format(
            schema=sql.Identifier(schema),
            table=sql.Identifier(table),
            geom=sql.Identifier(geometry_column),
        )
        cursor.execute(query)
        row = cursor.fetchone()
        if row and row["srid"]:
            result = int(row["srid"])
            log.debug("Finished resolve_srid.")
            return result
    except Exception as ex:
        log.info("Falling back to FALLBACK_EPSG because resolve_srid failed with exception: ", ex)

    log.debug("Finished resolve_srid using fallback.")
    return FALLBACK_EPSG


# ==========================================
# == helper: ensure a target-EPSG view   ===
# ==========================================


def ensure_target_view(
    cursor: psycopg.Cursor[Any],
    schema: str,
    table: str,
    id_column: str,
    geom_column: str,
    non_geom_properties: List[str],
    target_epsg: int,
) -> str:
    """Creates or replaces `<schema>.<table>__<target_epsg>` with geometry in target EPSG.

    Rules:
      * If row SRID = target → pass through.
      * If row SRID = 0 (unknown/None) → ST_SetSRID(..., target).
      * Otherwise (any other SRID or geography) → ST_Transform(..., target).

    Args:
        cursor: psycopg cursor.
        schema: Schema name.
        table: Base table name.
        id_column: Identifier column to project.
        geom_column: Geometry/geography column to transform/assign.
        non_geom_properties: Additional non-geometry property names.
        target_epsg: EPSG to normalize to.

    Returns:
        The created view name.
    """
    view_name = f"{table}__{int(target_epsg)}"
    props_no_id_geom = [p for p in non_geom_properties if p not in (id_column, geom_column)]

    id_ident = sql.Identifier(id_column).as_string(cursor)
    geom_ident = sql.Identifier(geom_column).as_string(cursor)

    geom_expr = f"""
        CASE
          WHEN ST_SRID({geom_ident}) = {int(target_epsg)} THEN {geom_ident}
          WHEN ST_SRID({geom_ident}) = 0 THEN ST_SetSRID({geom_ident}, {int(target_epsg)})
          ELSE ST_Transform(({geom_ident})::geometry, {int(target_epsg)})
        END AS {geom_ident}
    """

    select_parts = [id_ident, geom_expr] + [sql.Identifier(p).as_string(cursor) for p in props_no_id_geom]
    select_clause = ", ".join(select_parts)

    drop_sql = f"""
        DROP VIEW IF EXISTS
            {sql.Identifier(schema).as_string(cursor)}.{sql.Identifier(view_name).as_string(cursor)}
        CASCADE;
    """
    create_sql = f"""
        CREATE VIEW
            {sql.Identifier(schema).as_string(cursor)}.{sql.Identifier(view_name).as_string(cursor)}
        AS
        SELECT {select_clause}
        FROM {sql.Identifier(schema).as_string(cursor)}.{sql.Identifier(table).as_string(cursor)};
    """

    cursor.execute(drop_sql)
    cursor.execute(create_sql)
    log.debug("Finished ensure_target_view().")
    return view_name


# =========================
# ========= build =========
# =========================


def build_config_on_conn(connection: psycopg.Connection[Any]) -> None:
    """Scans DB, assembles pygeoapi config, and writes YAML atomically.

    Enumerates tables with a 'geom' column, normalizes to SERVICES_POSTGRES_EPSG
    via a helper view when needed, and writes a pygeoapi config referencing the
    base table or the helper view depending on SRID.

    Args:
        connection: psycopg connection.

    Returns:
        None. Writes pygeoapi-config.yml to OUTPUT_CONFIG_PATH.
    """
    log.debug("Executing build_config_on_conn() ...")
    skipped = 0
    with connection.cursor() as cursor:
        geometry_columns = list_geometry_sources(cursor)

        geometries_by_table: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
        for geom in geometry_columns:
            geometries_by_table[(geom["schema"], geom["table"])].append(geom)

        resources: Dict[str, Dict[str, Any]] = {}

        for (schema, table), geom_list in geometries_by_table.items():
            key = f"{schema}.{table}"

            # skip helper views
            if table.endswith(f"__{TARGET_EPSG}") or table.endswith("__crs84"):
                log.info("[SKIP] %s: generated helper view", key)
                skipped += 1
                continue

            # require a column literally named 'geom' (unchanged behavior)
            geometry_column_names = [g["geom_col"] for g in geom_list]
            if "geom" not in geometry_column_names:
                log.info("[SKIP] %s: no geometry column literally named 'geom'", key)
                skipped += 1
                continue

            id_field = pick_id_column(cursor, schema, table)
            if not id_field:
                log.info("[SKIP] %s: no column containing 'id'", key)
                skipped += 1
                continue

            geometry_column_entry = next(g for g in geom_list if g["geom_col"] == "geom")
            geom_field = "geom"

            srid_code = resolve_srid(
                cursor,
                schema=schema,
                table=table,
                geometry_column=geom_field,
                srid_hint=geometry_column_entry.get("srid"),
            )
            epsg_uri_detected = make_epsg_uri(srid_code)

            bbox_crs84: List[float] = GERMANY_BBOX_CRS84[:]

            columns = list_columns(cursor, schema, table)
            non_geom_properties = [name for name, typ in columns if typ not in ("geometry", "geography")]

            resource_id = f"{table}"
            resource_title = f"{table}"
            resource_description = f"{table}"
            keywords = [token for token in table.replace("-", "_").split("_") if token] or [table]

            table_value = table
            srid_code_effective = srid_code
            epsg_uri_effective = epsg_uri_detected

            try:
                # Normalize to TARGET_EPSG whenever detected SRID != TARGET_EPSG.
                if srid_code != TARGET_EPSG:
                    if (FORCE_DB_TRANSFORM_ALL or (key in _FORCE_SET)) and (key not in _EXCLUDES):
                        table_value = ensure_target_view(
                            cursor=cursor,
                            schema=schema,
                            table=table,
                            id_column=id_field,
                            geom_column=geom_field,
                            non_geom_properties=non_geom_properties,
                            target_epsg=TARGET_EPSG,
                        )
                    srid_code_effective = TARGET_EPSG
                    epsg_uri_effective = make_epsg_uri(TARGET_EPSG)
                else:
                    srid_code_effective = TARGET_EPSG
                    epsg_uri_effective = make_epsg_uri(TARGET_EPSG)

            except Exception as err:
                log.warning("[SKIP] %s: failed to create __%s view (%s)", key, TARGET_EPSG, err)
                skipped += 1
                continue

            advertised_crs = [CRS84_URI, epsg_uri_effective] if not FORCE_CRS84_ONLY else [CRS84_URI]

            provider_block = {
                "type": "feature",
                "name": "PostgreSQL",
                "data": {
                    "host": POSTGRES_HOST,
                    "port": POSTGRES_PORT,
                    "dbname": POSTGRES_DB,
                    "user": POSTGRES_USER,
                    "password": POSTGRES_PASSWORD,
                    "search_path": [schema],
                },
                "id_field": id_field,
                "table": table_value,
                "geom_field": geom_field,
                "geom_format": "geojson",
                "properties": [p for p in non_geom_properties if p != geom_field],
                "storage_crs": epsg_uri_effective,
                "crs": advertised_crs,
                "srid": srid_code_effective,
            }

            resources[resource_id] = {
                "type": "collection",
                "title": resource_title,
                "description": resource_description,
                "keywords": keywords,
                "extents": {
                    "spatial": {"bbox": bbox_crs84, "crs": CRS84_URI},
                    "temporal": {"begin": None, "end": None},
                },
                "providers": [provider_block],
            }

        # Write YAML atomically using shared helper (preserves original behavior)
        config_document: Dict[str, Any] = {
            "server": {
                "bind": {"host": "0.0.0.0", "port": PYGEOAPI_PORT},  # nosec B104
                "url": f"{PYGEOAPI_HOST}",
                "mimetype": "application/json; charset=UTF-8",
                "encoding": "utf-8",
                "gzip": False,
                "limit": 1000,
                "language": "en-US",
                "cors": True,
                "pretty_print": True,
                "admin": False,
                "limits": {"default_items": 10, "max_items": 50},
                "map": {
                    "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                    "attribution": (
                        '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
                    ),
                },
                "ogc_schemas_location": "/schemas.opengis.net",
            },
            "logging": {"level": "DEBUG"},
            "metadata": {
                "identification": {
                    "title": "pygeoapi Demo instance - running latest GitHub version",
                    "description": "pygeoapi provides an API to geospatial data",
                    "keywords": ["geospatial", "data", "api"],
                    "keywords_type": "theme",
                    "terms_of_service": "https://creativecommons.org/licenses/by/4.0/",
                    "url": "https://github.com/geopython/pygeoapi",
                },
                "license": {"name": "CC-BY 4.0 license", "url": "https://creativecommons.org/licenses/by/4.0/"},
                "provider": {"name": "pygeoapi Development Team", "url": "https://pygeoapi.io"},
                "contact": {
                    "name": "Infdb Development Team",
                    "position": "Developers",
                    "address": "Technical University of Munich",
                    "city": "Munich",
                },
            },
            "resources": resources,
        }

        atomic_write_yaml(config_document, str(OUTPUT_CONFIG_PATH))
        log.info(
            "Wrote %s with %d resource(s). Skipped %d table(s).", OUTPUT_CONFIG_PATH.resolve(), len(resources), skipped
        )


# =========================
# ======= main loop =======
# =========================


def listen_and_rebuild() -> None:
    """Connects, builds config, and rebuilds on schema/DML changes.

    Opens a persistent DB connection, builds the config, and then polls for
    schema/DML changes. Rebuilds the config when changes are detected, with a
    minimum rebuild gap to avoid thrashing.

    Returns:
        None. Runs indefinitely until interrupted.
    """
    log.debug("Executing listen_and_rebuild() ...")
    reconnect_backoff_seconds: float = 2
    poll_interval_seconds: float = 1.0
    min_rebuild_gap_seconds: float = 3.0
    log.info("starting pygeoapi config generation")
    while True:
        try:
            connection = psycopg.connect(DB_DSN, row_factory=dict_row)
            connection.autocommit = True

            build_config_on_conn(connection)
            last_schema_signature = get_schema_signature(connection)
            last_dml_signature = get_dml_signature_geom(connection)
            last_built_monotonic = time.monotonic()
            reconnect_backoff_seconds = 2

            while True:
                time.sleep(poll_interval_seconds)

                current_schema_signature = get_schema_signature(connection)
                current_dml_signature = get_dml_signature_geom(connection)

                schema_changed: bool = current_schema_signature != last_schema_signature
                dml_changed: bool = current_dml_signature != last_dml_signature
                enough_time_elapsed: bool = (time.monotonic() - last_built_monotonic) >= min_rebuild_gap_seconds

                if (schema_changed or dml_changed) and enough_time_elapsed:
                    build_config_on_conn(connection)
                    last_schema_signature = current_schema_signature
                    last_dml_signature = current_dml_signature
                    last_built_monotonic = time.monotonic()

        except psycopg.OperationalError as err:
            log.warning("DB connection problem: %s", err)
            time.sleep(reconnect_backoff_seconds)
            reconnect_backoff_seconds = min(reconnect_backoff_seconds * 2, 60)

        except Exception as err:
            log.error("Unexpected error in loop: %s", err)
            time.sleep(reconnect_backoff_seconds)
            reconnect_backoff_seconds = min(reconnect_backoff_seconds * 2, 60)


if __name__ == "__main__":
    try:
        listen_and_rebuild()
    except KeyboardInterrupt:
        pass
