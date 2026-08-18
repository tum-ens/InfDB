import logging
import subprocess
import time

from pyinfdb import InfDB
from sqlalchemy import text

from . import utils

log = logging.getLogger(__name__)


# ====================================================================================
# OpenStreetMap loader
# ====================================================================================
#   1. DOWNLOAD + FULL IMPORT (only if missing)
#      Launches the pgosm-flex container (osm2pgsql under the hood) as a
#      SIBLING container via the host Docker daemon. pgosm-flex downloads the WHOLE
#      subregion (e.g. Bavaria) from Geofabrik and imports it - in external Postgres
#      mode - directly into a STAGING schema (default "osm") of the infdb database.
#
#   2. SCOPE CLIP (every run)
#      Copies ONLY the features inside the configured scope from the staging schema into
#      the 'opendata' schema (opendata.osm_<table>).
# ====================================================================================

_PGOSM_IMAGE = "rustprooflabs/pgosm-flex"
_PGOSM_CONTAINER = "infdb_pgosm"
_PGOSM_VOLUME = "pgosm-data"  # caches the downloaded .osm.pbf between runs


# ------------------------------------------------------------------------------------
# Staging import (pgosm-flex) helpers
# ------------------------------------------------------------------------------------


def _staging_is_populated(conn, schema: str) -> bool:
    """True once pgosm-flex has finished: it writes a metadata table <schema>.pgosm_flex."""
    return bool(
        conn.execute(
            text(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :s AND table_name = 'pgosm_flex'
                """
            ),
            {"s": schema},
        ).scalar()
    )


def _wait_for_internal_pg(name: str, log, tries: int = 45, delay: int = 2) -> None:
    """Wait until the pgosm container's internal Postgres is up (needed before exec)."""
    for _ in range(tries):
        rc = subprocess.run(
            ["docker", "exec", name, "pg_isready", "-q"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        if rc == 0:
            return
        time.sleep(delay)
    log.warning("OSM: pgosm internal Postgres not ready after %ds; proceeding anyway.", tries * delay)


def _run_pgosm_import(infdb: InfDB, cfg: dict) -> None:
    """Run the two-step pgosm-flex workflow against the infdb database (external mode)."""
    log = infdb.get_worker_logger()
    p = infdb.get_db_parameters_dict()

    staging_schema = cfg["staging_schema"]

    # Remove any stale container left over from a previous failed run.
    utils.do_cmd(infdb, ["docker", "rm", "-f", _PGOSM_CONTAINER])

    # Step 1: start pgosm-flex (boots its internal Postgres, stays alive for exec).
    # POSTGRES_HOST != localhost => pgosm-flex will NOT drop/create the DB; it writes
    # into the already-running infdb database.
    run_cmd = [
        "docker", "run", "-d", "--name", _PGOSM_CONTAINER,
        # Let the container reach a host-published database via
        # 'host.docker.internal'; ignored when POSTGRES_HOST is a real IP.
        "--add-host", "host.docker.internal:host-gateway",
        "-e", f"POSTGRES_HOST={p['host']}",
        "-e", f"POSTGRES_PORT={p['exposed_port']}",
        "-e", f"POSTGRES_DB={p['db']}",
        "-e", f"POSTGRES_USER={p['user']}",
        "-e", f"POSTGRES_PASSWORD={p['password']}",
        "-v", f"{_PGOSM_VOLUME}:/app/output",
        _PGOSM_IMAGE,
    ]
    if utils.do_cmd(infdb, run_cmd) != 0:
        raise RuntimeError("OSM: failed to start pgosm-flex container")

    try:
        _wait_for_internal_pg(_PGOSM_CONTAINER, log)

        # Step 2: run the import (downloads the whole subregion, imports into staging).
        exec_cmd = [
            "docker", "exec", _PGOSM_CONTAINER,
            "python3", "docker/pgosm_flex.py",
            f"--ram={cfg['ram']}",
            f"--region={cfg['region']}",
            f"--subregion={cfg['subregion']}",
            f"--layerset={cfg['layerset']}",
            f"--schema-name={staging_schema}",
            f"--srid={cfg['srid']}",
        ]
        log.info(
            "OSM: staging schema '%s' missing -> importing whole %s/%s via pgosm-flex "
            "(this downloads the full subregion and can take a while)...",
            staging_schema,
            cfg["region"],
            cfg["subregion"],
        )
        if utils.do_cmd(infdb, exec_cmd) != 0:
            raise RuntimeError("OSM: pgosm_flex.py import failed")
    finally:
        # Always remove the helper container; the .osm.pbf stays cached in the volume.
        utils.do_cmd(infdb, ["docker", "rm", "-f", _PGOSM_CONTAINER])


# ------------------------------------------------------------------------------------
# Scope clip helpers
# ------------------------------------------------------------------------------------


def _list_base_tables(conn, schema: str) -> list[str]:
    """Return all base table names in the given schema (materialized views excluded)."""
    return list(
        conn.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = :schema AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """
            ),
            {"schema": schema},
        )
        .scalars()
        .all()
    )


def _spatial_columns(conn, schema: str) -> dict[str, tuple[str, int]]:
    """Map every spatial table to its (geometry_column, srid) via geometry_columns."""
    rows = conn.execute(
        text(
            """
            SELECT f_table_name, f_geometry_column, srid
            FROM geometry_columns
            WHERE f_table_schema = :schema
            """
        ),
        {"schema": schema},
    ).all()
    return {r[0]: (r[1], int(r[2])) for r in rows}


# ------------------------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------------------------


def load(infdb: InfDB) -> bool:
    """Ensure OSM data is present (download whole subregion if missing), then clip to scope."""
    log = infdb.get_worker_logger()

    try:
        if not utils.if_active("osm", infdb):
            return True

        source_cfg = [infdb.get_toolname(), "sources", "osm"]
        cfg = {
            "staging_schema": infdb.get_config_value(source_cfg + ["staging_schema"]) or "osm",
            "schema": infdb.get_config_value(source_cfg + ["schema"]) or "opendata",
            "prefix": infdb.get_config_value(source_cfg + ["prefix"]) or "osm",
            "srid": int(infdb.get_config_value(source_cfg + ["srid"]) or 25832),
            "region": infdb.get_config_value(source_cfg + ["region"]) or "europe/germany",
            "subregion": infdb.get_config_value(source_cfg + ["subregion"]) or "bayern",
            "layerset": infdb.get_config_value(source_cfg + ["layerset"]) or "everything",
            "ram": infdb.get_config_value(source_cfg + ["ram"]) or 8,
        }
        staging_schema = cfg["staging_schema"]
        target_schema = cfg["schema"]
        prefix = cfg["prefix"]
        srid = cfg["srid"]

        engine = infdb.get_db_engine()

        # ---------- 1. Download + import the whole subregion if not present yet ----------
        with engine.connect() as conn:
            already_present = _staging_is_populated(conn, staging_schema)

        if not already_present:
            _run_pgosm_import(infdb, cfg)
            with engine.connect() as conn:
                if not _staging_is_populated(conn, staging_schema):
                    log.warning("OSM: staging schema '%s' still not populated after import; skipping.", staging_schema)
                    return True
        else:
            log.info("OSM: staging schema '%s' already present; skipping download.", staging_schema)

        # ---------- 2. Resolve scope geometry (uses global config 'scope:' list) ----------
        clip_wkt, _, _ = utils.get_clip_geometry(target_crs=srid, infdb=infdb)
        if not clip_wkt:
            log.warning("OSM: no scope geometry resolved; skipping OSM scope clip.")
            return True

        # ---------- 3. Materialize scope geometry once (indexed) for fast joins ----------
        scope_table = f"_{prefix}_scope"
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {target_schema};"))
            conn.execute(text(f"DROP TABLE IF EXISTS {target_schema}.{scope_table};"))
            conn.execute(
                text(f"CREATE TABLE {target_schema}.{scope_table} (geom geometry(Geometry, {srid}));")
            )
            conn.execute(
                text(
                    f"INSERT INTO {target_schema}.{scope_table} (geom) "
                    f"VALUES (ST_GeomFromText(:wkt, {srid}));"
                ),
                {"wkt": clip_wkt},
            )
            conn.execute(text(f"CREATE INDEX ON {target_schema}.{scope_table} USING GIST (geom);"))
            conn.commit()

            tables = _list_base_tables(conn, staging_schema)
            spatial = _spatial_columns(conn, staging_schema)

        log.info(
            "OSM: %d staging tables in '%s' (%d spatial) -> clipping into '%s'.",
            len(tables),
            staging_schema,
            len(spatial),
            target_schema,
        )

        # ---------- 4. Copy each table into the target schema ----------
        clipped, copied = 0, 0
        for tbl in tables:
            dest = f"{prefix}_{tbl}"
            with engine.connect() as conn:
                conn.execute(text(f'DROP TABLE IF EXISTS {target_schema}."{dest}";'))

                if tbl in spatial:
                    geom_col, tsrid = spatial[tbl]
                    # Keep only features intersecting the scope. Everything was
                    # imported with --srid, but some pgosm tables (e.g.
                    # place_polygon_nested) declare SRID 0 in geometry_columns.
                    # - unknown (0) or already == srid: label the staged geom as
                    #   `srid` and compare against the scope directly.
                    # - a different, valid SRID: transform the scope to it.
                    if tsrid and tsrid > 0 and tsrid != srid:
                        t_geom = f't."{geom_col}"'
                        s_geom = f"ST_Transform(s.geom, {tsrid})"
                    else:
                        t_geom = f'ST_SetSRID(t."{geom_col}", {srid})'
                        s_geom = "s.geom"
                    conn.execute(
                        text(
                            f'CREATE TABLE {target_schema}."{dest}" AS '
                            f'SELECT t.* FROM {staging_schema}."{tbl}" t '
                            f'JOIN {target_schema}.{scope_table} s '
                            f"ON ST_Intersects({t_geom}, {s_geom});"
                        )
                    )
                    conn.execute(
                        text(f'CREATE INDEX ON {target_schema}."{dest}" USING GIST ("{geom_col}");')
                    )
                    clipped += 1
                else:
                    # Non-spatial metadata / lookup tables: copy in full.
                    conn.execute(
                        text(
                            f'CREATE TABLE {target_schema}."{dest}" AS '
                            f'SELECT * FROM {staging_schema}."{tbl}";'
                        )
                    )
                    copied += 1
                conn.commit()

        # ---------- 5. Clean up helper objects ----------
        with engine.connect() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {target_schema}.{scope_table};"))
            # pgosm-flex auto-creates the 'pgosm' schema (routing reference table);
            # routing is currently not used, so drop it.
            conn.execute(text("DROP SCHEMA IF EXISTS pgosm CASCADE;"))
            conn.commit()

        log.info(
            "OSM: done. %d spatial tables clipped, %d non-spatial copied into '%s'.",
            clipped,
            copied,
            target_schema,
        )
        return True

    except Exception as err:
        log.exception("An error occurred while processing OSM data: %s", str(err))
        return False
