import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

import psycopg2
import yaml
from dotenv import load_dotenv

# Constants
HERE = Path(__file__).resolve().parent
PARENT_PATH = HERE.parent
SCHEMA_PATH = HERE / "schema.yaml"
BASE_IRI = os.getenv("IRI_BASE", "https://id.need.energy/dataschema")

# Logger
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# Functions
def load_env(log) -> None:
    """Load environment variables from a .env file in the parent directory.

    Args:
        log: Logger instance.
    """
    log.info("Loading environment variables...")
    load_dotenv(PARENT_PATH / ".env")


def make_iri(*parts: str) -> str:
    """Construct an IRI by joining the base IRI with encoded parts."""
    base = BASE_IRI.rstrip("/")
    encoded_parts = [quote(str(p), safe="") for p in parts]
    return "/".join([base, *encoded_parts])


def get_conn(log) -> psycopg2.extensions.connection:
    """Establish a connection to the PostgreSQL database using environment variables.

    Args:
        log: Logger instance.
    """
    db_url = os.getenv("DB_URL")
    if db_url:
        return psycopg2.connect(db_url)
    params = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "dbname": os.getenv("DB_NAME"),
        "connect_timeout": os.getenv("DB_CONNECT_TIMEOUT", "30"),
    }
    log.info(params)

    if not params["user"] or not params["password"] or not params["dbname"]:
        raise RuntimeError(
            "Missing database connection information. Please set DB_URL "
            "or DB_HOST/DB_USER/DB_PASSWORD/DB_NAME in the .env file."
        )
    log.info("Connecting to database...")
    return psycopg2.connect(**params)


def _fetch_columns(cur, schema: str, table: str) -> List[Dict[str, object]]:
    """Fetch column metadata for a given schema and table.

    Args:
        cur: Database cursor.
        schema: Schema name.
        table: Table name.

    Returns:
        List of column metadata dictionaries.
    """
    cur.execute(
        """
        SELECT table_catalog, table_schema, table_name, column_name, data_type,
                is_nullable, column_default, ordinal_position
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """,
        (schema, table),
    )
    columns = []
    for (
        table_catalog,
        table_schema,
        table_name,
        column_name,
        data_type,
        is_nullable,
        column_default,
        ordinal_position,
    ) in cur.fetchall():
        columns.append(
            {
                "table_catalog": table_catalog,
                "table_schema": table_schema,
                "table_name": table_name,
                "column_name": column_name,
                "data_type": data_type,
                "is_nullable": is_nullable == "YES",
                "column_default": column_default,
                "ordinal_position": int(ordinal_position),
            }
        )
    return columns


def _fetch_columns_infdb(infdb_client, schema: str, table: str) -> List[Dict[str, object]]:
    """Fetch column metadata for a given schema and table.

    Args:
        infdb_client: InfDB client instance.
        schema: Schema name.
        table: Table name.

    Returns:
        List of column metadata dictionaries.
    """
    fetched = infdb_client.execute_query(
        """
        SELECT table_catalog, table_schema, table_name, column_name, 
            data_type, is_nullable, column_default, ordinal_position
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """,
        (schema, table),
    )
    columns = []
    for (
        table_catalog,
        table_schema,
        table_name,
        column_name,
        data_type,
        is_nullable,
        column_default,
        ordinal_position,
    ) in fetched:
        columns.append(
            {
                "table_catalog": table_catalog,
                "table_schema": table_schema,
                "table_name": table_name,
                "column_name": column_name,
                "data_type": data_type,
                "is_nullable": is_nullable == "YES",
                "column_default": column_default,
                "ordinal_position": int(ordinal_position),
            }
        )
    return columns


def fetch_metadata(log, conn: psycopg2.extensions.connection) -> Dict[str, object]:
    """Fetch database schema metadata.

    Args:
        log: Logger instance.
        conn: Database connection.

    Returns:
        Database metadata dictionary.
    """
    log.info("Fetching schema and table list...")
    cur = conn.cursor()
    db_name: Optional[str] = conn.get_dsn_parameters().get("dbname") if hasattr(conn, "get_dsn_parameters") else None
    db_name = db_name or os.getenv("DB_NAME") or os.getenv("POSTGRES_DB") or "database"

    cur.execute(
        """
        SELECT catalog_name, schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
        AND schema_name NOT LIKE '_timescaledb_%'
        AND schema_name NOT LIKE 'pg_toast%'
        AND schema_name NOT LIKE 'pg_temp%'
        ORDER BY schema_name
        """
    )
    schema_rows = cur.fetchall()

    cur.execute(
        """
        SELECT table_catalog, table_schema, table_name, table_type
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name
        """
    )
    table_rows = cur.fetchall()

    tables_by_schema: Dict[str, List[tuple]] = {}
    for table_catalog, table_schema, table_name, table_type in table_rows:
        tables_by_schema.setdefault(table_schema, []).append((table_catalog, table_schema, table_name, table_type))

    schemas: Dict[str, Dict[str, object]] = {}
    for catalog_name, schema_name in schema_rows:
        log.info(f"  Processing schema: {schema_name}")
        schema_entry = schemas.setdefault(
            schema_name,
            {
                "id": make_iri("schema", db_name, schema_name),
                "catalog_name": catalog_name,
                "schema_name": schema_name,
                "tables": [],
            },
        )
        for table_schema, table_name, table_type in tables_by_schema.get(schema_name, []):
            # NOTE: print out tables in a schema
            # print(f"    Table: {table_name}", flush=True)
            columns = _fetch_columns(cur, table_schema, table_name)
            for col in columns:
                col["id"] = make_iri("column", db_name, table_schema, table_name, col["column_name"])

            cur.execute(
                """
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = %s
                    AND tc.table_name = %s
                ORDER BY kcu.ordinal_position
                """,
                (table_schema, table_name),
            )
            pk_names = [row[0] for row in cur.fetchall()]
            column_by_name = {c["column_name"]: c for c in columns}
            primary_key = [column_by_name[name] for name in pk_names if name in column_by_name]

            table_entry = {
                "id": make_iri("table", db_name, table_schema, table_name),
                "table_name": table_name,
                "table_type": table_type,
                "columns": columns,
                "primary_key": primary_key,
            }
            schema_entry["tables"].append(table_entry)

    cur.close()

    if not schemas:
        return {}

    return {
        "id": make_iri("database", db_name),
        "name": db_name,
        "schemas": list(schemas.values()),
    }


def fetch_metadata_infdb(log, infdb_client) -> Dict[str, object]:
    """Fetch database schema metadata.

    Args:
        log: Logger instance.
        infdb_client: InfDB client instance.

    Returns:
        Database metadata dictionary.
    """
    log.info("Fetching schema and table list...")
    db_name = os.getenv("DB_NAME")

    schema_rows = infdb_client.execute_query(
        """
        SELECT catalog_name, schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
        AND schema_name NOT LIKE '_timescaledb_%'
        AND schema_name NOT LIKE 'pg_toast%'
        AND schema_name NOT LIKE 'pg_temp%'
        ORDER BY schema_name
        """
    )

    table_rows = infdb_client.execute_query(
        """
        SELECT table_catalog, table_schema, table_name, table_type
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name
        """
    )
    # table_rows = cur.fetchall()

    tables_by_schema: Dict[str, List[tuple]] = {}
    for table_catalog, table_schema, table_name, table_type in table_rows:
        tables_by_schema.setdefault(table_schema, []).append((table_catalog, table_schema, table_name, table_type))

    schemas: Dict[str, Dict[str, object]] = {}
    for catalog_name, schema_name in schema_rows:
        log.info(f"  Processing schema: {schema_name}")
        schema_entry = schemas.setdefault(
            schema_name,
            {
                "id": make_iri("schema", db_name, schema_name),
                "catalog_name": catalog_name,
                "schema_name": schema_name,
                "tables": [],
            },
        )
        for table_schema, table_name, table_type in tables_by_schema.get(schema_name, []):
            # NOTE: print out tables in a schema
            # print(f"    Table: {table_name}", flush=True)
            columns = _fetch_columns_infdb(infdb_client, table_schema, table_name)
            for col in columns:
                col["id"] = make_iri("column", db_name, table_schema, table_name, col["column_name"])

            pk_names_fetched = infdb_client.execute_query(
                """
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = %s
                    AND tc.table_name = %s
                ORDER BY kcu.ordinal_position
                """,
                (table_schema, table_name),
            )
            pk_names = [row[0] for row in pk_names_fetched]
            column_by_name = {c["column_name"]: c for c in columns}
            primary_key = [column_by_name[name] for name in pk_names if name in column_by_name]

            table_entry = {
                "id": make_iri("table", db_name, table_schema, table_name),
                "table_name": table_name,
                "table_type": table_type,
                "columns": columns,
                "primary_key": primary_key,
            }
            schema_entry["tables"].append(table_entry)

    if not schemas:
        return {}

    return {
        "id": make_iri("database", db_name),
        "name": db_name,
        "schemas": list(schemas.values()),
    }


def print_available_schemas(log, metadata: Dict[str, object]) -> List[str]:
    """Print available schemas from the metadata.

    Args:
        log: Logger instance.
        metadata: The database metadata dictionary.

    Returns:
        List of schema names.
    """
    schemas = [s.get("schema_name") for s in metadata.get("schemas", [])]
    if not schemas:
        log.error("No user schemas found in the database; nothing to export.")
        return []
    log.info("Available schemas:")
    for name in schemas:
        log.info(f"  - {name}")
    return schemas


def prompt_schema_selection(log, available: List[str]) -> Optional[List[str]]:
    """Prompt the user to select schemas.

    Args:
        log: Logger instance.
        available: List of available schema names.

    Returns:
        List of selected schema names, or None for all.
    """
    log.info("Awaiting schema selection...")
    try:
        raw = input("Enter schema names separated by commas (leave empty or type 'all' for all): ").strip()
    except EOFError:
        # Non-interactive environment; default to all
        return None
    if not raw or raw.lower() == "all":
        return None
    parts = [p.strip() for p in raw.replace(",", " ").split() if p.strip()]
    return parts or None


def filter_schemas(metadata: Dict[str, object], schemas: Optional[List[str]]) -> Dict[str, object]:
    """Filter metadata to include only specified schemas.

    Args:
        metadata: The database metadata dictionary.
        schemas: List of schema names to include.

    Returns:
        Filtered database metadata dictionary.
    """
    if not schemas:
        return metadata
    wanted = {s.strip() for s in schemas if s.strip()}
    filtered = [s for s in metadata.get("schemas", []) if s.get("schema_name") in wanted]
    return {**metadata, "schemas": filtered}


def write_metadata_file(log, data: Dict[str, object], path: Path, quiet: bool = False) -> None:
    """Write metadata to a JSON file.

    Args:
        log: Logger instance.
        data: The metadata dictionary to write.
        path: The file path to write the JSON data to.
        quiet: If True, suppress output messages.
    """
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    if not quiet:
        log.info(f"✅ Saved LinkML-shaped metadata to {path}")


def write_metadata_yaml(log, data: Dict[str, object], path: Path) -> None:
    """Write metadata to a YAML file.

    Args:
        log: Logger instance.
        data: The metadata dictionary to write.
        path: The file path to write the YAML data to.
    """
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)
    log.info(f"✅ Saved LinkML-shaped metadata to {path}")


def wrap_database(metadata: Dict[str, object]) -> Dict[str, object]:
    """Wrap metadata in a top-level 'Database' key.

    Args:
        metadata: The database metadata dictionary.

    Returns:
        Wrapped metadata dictionary.
    """
    return {"Database": metadata}


def generate_rdf(log, schema_path: Path, data_path: Path, output_path: Path) -> Path:
    """Generate RDF (TTL) from LinkML JSON using linkml-convert.

    Args:
        log: Logger instance.
        schema_path: Path to the LinkML schema file.
        data_path: Path to the LinkML JSON data file.
        output_path: Path to write the RDF (TTL) output.

    Returns:
        Path to the generated RDF (TTL) file.
    """
    log.info("Generating RDF (TTL) via linkml-convert...")
    cmd_path = shutil.which("linkml-convert")
    if cmd_path is None:
        candidate = Path(sys.executable).parent / "linkml-convert"
        cmd_path = str(candidate) if candidate.exists() else None
    if cmd_path is None:
        raise RuntimeError("linkml-convert command not found. Install LinkML with `pip install linkml`.")

    cmd = [
        cmd_path,
        str(data_path),
        "--schema",
        str(schema_path),
        "--target-class",
        "Database",
        "--output",
        str(output_path),
        "--output-format",
        "ttl",
    ]
    try:
        completed = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        if completed.stdout:
            log.info(completed.stdout.strip())
    except FileNotFoundError as exc:
        raise RuntimeError("linkml-convert command not available") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else ""
        raise RuntimeError(f"linkml-convert failed: {stderr or exc}") from exc

    log.info(f"✅ Generated RDF at {output_path}")
    return output_path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(description="Export PostgreSQL schema metadata in LinkML JSON and TTL formats.")
    parser.add_argument(
        "--schemas",
        nargs="+",
        help="One or more schema names to include (default: all non-system schemas).",
    )
    return parser.parse_args()


def run(log) -> int:
    """Main execution function.

    Args:
        log: Logger instance.
    """
    args = parse_args()
    load_env(log)
    try:
        conn = get_conn(log)
    except Exception as exc:
        log.error(f"Failed to connect to database: {exc}")
        return 1

    try:
        metadata = fetch_metadata(log, conn)
    finally:
        conn.close()
    log.info("✅ Finished fetching metadata.")

    available_schemas = print_available_schemas(log, metadata)
    if not available_schemas:
        return 0

    chosen = args.schemas
    if not chosen:
        chosen = prompt_schema_selection(log, available_schemas)

    if chosen:
        log.info("Filtering to selected schemas...")
    metadata = filter_schemas(metadata, chosen)

    selected_schemas = [s.get("schema_name") for s in metadata.get("schemas", [])]
    log.info(selected_schemas)
    if chosen and not selected_schemas:
        log.error(f"No matching schemas found for: {', '.join(chosen)}")
        return 1
    if chosen:
        log.info(f"Including schemas: {', '.join(selected_schemas)}")
    db_label = metadata.get("name") or "database"

    # NOTE: to make sure the output is writable in containerized environments,
    # write to OUTPUT_DIR or /app/mnt/data in a docker by default
    out_base = Path(os.getenv("OUTPUT_DIR", "/app/mnt/data"))
    out_base.mkdir(parents=True, exist_ok=True)

    # NOTE: revert to naming without schema names in suffix
    # suffix = ""
    # if selected_schemas:
    #     suffix = "-" + "-".join(selected_schemas)
    # data_path = out_base / f"{db_label}{suffix}_schema.json"
    # yaml_path = out_base / f"{db_label}{suffix}_schema.yaml"

    data_path = out_base / f"{db_label}_schema.json"
    yaml_path = out_base / f"{db_label}_schema.yaml"
    wrapped = wrap_database(metadata)
    log.info("Writing JSON and YAML outputs...")
    write_metadata_file(log, wrapped, data_path)
    write_metadata_yaml(log, wrapped, yaml_path)

    rdf_input_path = Path(tempfile.mkstemp(prefix="rdf_input_", suffix=".json", dir=str(HERE))[1])
    try:
        write_metadata_file(log, metadata, rdf_input_path, quiet=True)
        # with open (rdf_input_path, "r", encoding="utf-8") as fh:
        #     print(fh.read())

        rdf_output = data_path.with_suffix(".ttl")
        try:
            generate_rdf(log, SCHEMA_PATH, rdf_input_path, rdf_output)
        except Exception as exc:
            log.error(f"Skipping RDF generation because LinkML tooling is unavailable: {exc}")
            log.info(
                "To generate RDF manually, run "
                f"`linkml-convert {rdf_input_path} --schema {SCHEMA_PATH} "
                f"--target-class Database --output {rdf_output} --output-format ttl`."
            )
    finally:
        try:
            rdf_input_path.unlink()
        except OSError:
            pass
    return 0


def run_with_infdb(infdb_client, log) -> int:
    """Main execution function with InfDB client.

    Args:
        infdb_client: InfDB client instance.
        log: Logger instance.
    """
    args = parse_args()
    try:
        metadata = fetch_metadata_infdb(log, infdb_client)
    except Exception as exc:
        log.error(f"Failed to connect to database or fetch metadata: {exc}")
        return 1
    log.info("✅ Finished fetching metadata.")

    available_schemas = print_available_schemas(log, metadata)
    if not available_schemas:
        return 0

    chosen = args.schemas
    if not chosen:
        chosen = prompt_schema_selection(log, available_schemas)

    if chosen:
        log.info("Filtering to selected schemas...")
    metadata = filter_schemas(metadata, chosen)

    selected_schemas = [s.get("schema_name") for s in metadata.get("schemas", [])]
    log.info(selected_schemas)
    if chosen and not selected_schemas:
        log.error(f"No matching schemas found for: {', '.join(chosen)}")
        return 1
    if chosen:
        log.info(f"Including schemas: {', '.join(selected_schemas)}")
    db_label = metadata.get("name") or "database"

    out_base = Path(os.getenv("OUTPUT_DIR", "/app/mnt/data"))
    out_base.mkdir(parents=True, exist_ok=True)

    data_path = out_base / f"{db_label}_schema.json"
    yaml_path = out_base / f"{db_label}_schema.yaml"
    wrapped = wrap_database(metadata)
    log.info("Writing JSON and YAML outputs...")
    write_metadata_file(log, wrapped, data_path)
    write_metadata_yaml(log, wrapped, yaml_path)

    rdf_input_path = Path(tempfile.mkstemp(prefix="rdf_input_", suffix=".json", dir=str(HERE))[1])
    try:
        write_metadata_file(log, metadata, rdf_input_path, quiet=True)

        rdf_output = data_path.with_suffix(".ttl")
        try:
            generate_rdf(log, SCHEMA_PATH, rdf_input_path, rdf_output)
        except Exception as exc:
            log.error(f"Skipping RDF generation because LinkML tooling is unavailable: {exc}")
            log.info(
                "To generate RDF manually, run "
                f"`linkml-convert {rdf_input_path} --schema {SCHEMA_PATH} "
                f"--target-class Database --output {rdf_output} --output-format ttl`."
            )
    finally:
        try:
            rdf_input_path.unlink()
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(run())
