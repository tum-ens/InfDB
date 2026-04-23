import logging
import pathlib
import re
import time
from datetime import datetime, timezone
from typing import Iterable

import psycopg
from infdb import InfDB
import utils
from psycopg import Connection
from psycopg.rows import dict_row

infdb = InfDB(tool_name="infdb-postgrest", config_path="config-infdb-postgrest.yml")
# ============================== Logging ==============================
log = infdb.get_worker_logger()
if not log.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


# ============================== Defaults & regex ==============================

DEFAULT_WATCH_INTERVAL_SECONDS: float = 1.0
DEFAULT_MIN_RELOAD_GAP_SECONDS: float = 3.0
DEFAULT_CHANNEL: str = "pgrst"
DEFAULT_EXCLUDE_SCHEMAS_CSV: str = "pg_*,information_schema,postgrest"
DEFAULT_CONF_PATH: str = "/workspaces/postgrest/postgrest.conf"

CONF_LINE_RE = re.compile(r'^\s*db-schemas\s*=\s*"(?:[^"\\]|\\.)*"\s*$', re.MULTILINE)


# ============================== Runtime config (cached once) ==============================


POSTGRES_HOST: str = str(utils.read_env("SERVICES_POSTGRES_HOST", required=True))
POSTGRES_PORT_STRING: str = str(utils.read_env("SERVICES_POSTGRES_EXPOSED_PORT", required=True))
POSTGRES_USER: str = str(utils.read_env("SERVICES_POSTGRES_USER", required=True))
POSTGRES_PASSWORD: str = str(utils.read_env("SERVICES_POSTGRES_PASSWORD", required=True))
POSTGRES_DB: str = str(utils.read_env("SERVICES_POSTGRES_DB", required=True))
if POSTGRES_PORT_STRING is None:
    raise ValueError("SERVICES_POSTGRES_EXPOSED_PORT is required but not provided.")
POSTGRES_PORT: int = int(POSTGRES_PORT_STRING)

POSTGREST_PORT_STRING: str = str(utils.read_env("SERVICES_POSTGREST_PORT", required=True))
if POSTGREST_PORT_STRING is None:
    raise ValueError("SERVICES_POSTGREST_PORT is required but not provided.")
POSTGREST_PORT: int = int(POSTGREST_PORT_STRING)


DSN: str = utils.build_dsn_from_env(
    user_var=POSTGRES_USER,
    pwd_var=POSTGRES_PASSWORD,
    db_var=POSTGRES_DB,
    host_var=POSTGRES_HOST,
    port_var=POSTGRES_PORT,
)

CHANNEL: str = DEFAULT_CHANNEL
POLL_INTERVAL_SECONDS: float = DEFAULT_WATCH_INTERVAL_SECONDS
MIN_REBUILD_GAP_SECONDS: float = DEFAULT_MIN_RELOAD_GAP_SECONDS

EXCLUDE_SCHEMAS: list[str] = [s.strip() for s in DEFAULT_EXCLUDE_SCHEMAS_CSV.split(",") if s.strip()]

# File/dir modes (read once)
CONF_FILE_MODE_STR: str = str(utils.read_env("POSTGREST_CONF_MODE", default="0644"))
CONF_DIR_MODE_STR: str = str(utils.read_env("POSTGREST_CONF_DIR_MODE", default="0755"))


def resolve_conf_path() -> tuple[pathlib.Path, pathlib.Path]:
    """Resolves the config file path and its directory."""
    conf_path_env = DEFAULT_CONF_PATH
    conf_path = pathlib.Path(conf_path_env)
    if conf_path.is_dir():
        conf_dir = conf_path
        conf_path = conf_dir / "postgrest.conf"
    else:
        conf_dir = conf_path.parent
    return conf_path, conf_dir


CONF_PATH, CONF_DIR = resolve_conf_path()


# ============================== FS helpers (using utils) ==============================


def utcnow() -> str:
    """Returns the current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def atomic_write_text(text: str, out_path: pathlib.Path) -> None:
    """Atomically writes text to the given path and sets modes from env.

    We delegate the actual safe write to utils.atomic_write_text,
    but still apply the file/dir modes that this watcher cares about.
    This preserves your original behavior.
    """
    utils.atomic_write_text(
        text,
        str(out_path),
        file_mode=CONF_FILE_MODE_STR,
        dir_mode=CONF_DIR_MODE_STR,
    )


def read_text(path: pathlib.Path) -> str:
    """Reads a file as text, returning empty string if missing.

    This is now just a thin wrapper around utils.read_text to keep the
    call sites unchanged.
    """
    return utils.read_text(str(path))


# ============================== Config rendering ==============================


def ensure_conf_exists(conf_path: pathlib.Path, conf_dir: pathlib.Path) -> None:
    """Ensures the PostgREST config file exists; creates a minimal one if missing.

    Leaves `db-schemas` empty so this script remains the single source of truth later.
    """
    if conf_path.exists() and conf_path.is_file():
        return

    conf_dir.mkdir(parents=True, exist_ok=True)

    # Build defaults (prefer explicit URIs if set; otherwise use globals)
    db_uri = DSN
    anon_role = POSTGRES_USER
    port = POSTGREST_PORT

    default_conf = f'db-uri = "{db_uri}"\ndb-anon-role = "{anon_role}"\nserver-port = {port}\ndb-schemas = ""\n'
    atomic_write_text(default_conf, conf_path)
    print(f"[{utcnow()}] created {conf_path} with minimal defaults")


def fnmatch_any(name: str, patterns: Iterable[str]) -> bool:
    """Returns True if `name` matches any of the glob `patterns`."""
    import fnmatch

    return any(fnmatch.fnmatch(name, p) for p in patterns)


def get_user_schemas(conn: Connection[dict]) -> list[str]:
    """Returns non-system schema names, filtered by EXCLUDE_SCHEMAS."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT nspname
            FROM pg_namespace
            WHERE nspname NOT LIKE 'pg_%'
              AND nspname <> 'information_schema'
            ORDER BY nspname;
            """
        )
        rows = cur.fetchall()
    schemas = [r["nspname"] for r in rows]
    return [s for s in schemas if not fnmatch_any(s, EXCLUDE_SCHEMAS)]


def render_conf_with_schemas(original: str, schemas_csv: str) -> str:
    """Renders a config text with a (single) db-schemas line containing `schemas_csv`."""
    line = f'db-schemas = "{schemas_csv}"'
    if CONF_LINE_RE.search(original):
        return CONF_LINE_RE.sub(line, original, count=1)
    if original and not original.endswith("\n"):
        original += "\n"
    return original + line + "\n"


def notify_postgrest_reload(conn: Connection[dict], channel: str) -> None:
    """Notifies PostgREST over LISTEN/NOTIFY to reload config and schema cache."""
    with conn.cursor() as cur:
        cur.execute("SELECT pg_notify(%s, 'reload config')", (channel,))
        cur.execute("SELECT pg_notify(%s, 'reload schema')", (channel,))


# ============================== Main loop ==============================


def loop() -> None:
    """Watches DB schemas; updates PostgREST config and notifies on changes."""
    backoff_seconds = 2.0
    last_signature = ""
    last_reload_monotonic = 0.0

    while True:
        try:
            # Ensure config file exists before doing anything else
            ensure_conf_exists(CONF_PATH, CONF_DIR)

            with psycopg.connect(DSN, row_factory=dict_row) as conn:
                conn.autocommit = True
                print(f"[{utcnow()}] Connected; watching schemas → {CONF_PATH}")

                # Initial apply
                schemas = get_user_schemas(conn)
                # use utils' stable signature builder
                signature = utils.compute_signature(schemas)
                conf_text = read_text(CONF_PATH)
                new_conf_text = render_conf_with_schemas(conf_text, ",".join(schemas))
                if new_conf_text != conf_text:
                    atomic_write_text(new_conf_text, CONF_PATH)
                    print(f"[{utcnow()}] wrote {CONF_PATH} (schemas: {schemas or '∅'})")
                    notify_postgrest_reload(conn, CHANNEL)
                    last_reload_monotonic = time.monotonic()
                last_signature = signature
                backoff_seconds = 2.0

                # Poll loop
                while True:
                    time.sleep(POLL_INTERVAL_SECONDS)
                    schemas = get_user_schemas(conn)
                    signature = utils.compute_signature(schemas)
                    enough_time_elapsed = (time.monotonic() - last_reload_monotonic) >= MIN_REBUILD_GAP_SECONDS
                    if signature != last_signature and enough_time_elapsed:
                        conf_text = utils.read_text(CONF_PATH)
                        new_conf_text = render_conf_with_schemas(conf_text, ",".join(schemas))
                        if new_conf_text != conf_text:
                            utils.atomic_write_text(new_conf_text, CONF_PATH)
                            print(f"[{utcnow()}] schemas changed → {schemas or '∅'}; updated config")
                            notify_postgrest_reload(conn, CHANNEL)
                            last_reload_monotonic = time.monotonic()
                        else:
                            print(f"[{utcnow()}] schemas changed but config already in sync")
                        last_signature = signature

        except psycopg.OperationalError as err:
            print(f"[WARN] DB connection problem: {err}")
            time.sleep(backoff_seconds)
            backoff_seconds = min(backoff_seconds * 2, 60)
        except Exception as err:
            print(f"[ERR] Unexpected error: {err}")
            time.sleep(backoff_seconds)
            backoff_seconds = min(backoff_seconds * 2, 60)


if __name__ == "__main__":
    try:
        loop()
    except KeyboardInterrupt:
        print("Exiting.")
