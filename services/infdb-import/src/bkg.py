# src/bkg.py
import os
from typing import Sequence, Union

from infdb import InfDB

from . import utils


def create_geogitter(resolutions: Union[Sequence[str], str], infdb: InfDB, clear_existing: bool = False) -> None:
    """Creates (or updates) a single geogitter table by inserting grid cells per resolution.

    Behavior preserved:
    - Single target table: {schema}.{table_name}
    - Optionally drop the table when `clear_existing=True`
    - Create schema + spatial index if missing
    - Insert grid cells per resolution, skipping rows whose id already exists

    Args:
        resolutions: Either a single resolution string (e.g., "1km", "500m")
            or a sequence of such strings.
        infdb: The InfDB instance.
        clear_existing: If True, drop the table before (re)creating it.

    Raises:
        KeyError: If EPSG is missing in DB parameters.
    """
    log = infdb.get_worker_logger()
    # DB / config
    epsg = (infdb.get_db_parameters_dict() or {}).get("epsg")
    if epsg is None:
        raise KeyError("Missing 'epsg' in DB parameters for service 'postgres'")
    schema = infdb.get_config_value([infdb.get_toolname(), "sources", "bkg", "schema"])
    table_name = infdb.get_config_value([infdb.get_toolname(), "sources", "bkg", "geogitter", "table_name"])

    # Build base table
    with infdb.connect() as db:
        if clear_existing:
            log.info("Dropping existing geogitter table %s.%s ...", schema, table_name)
            db.execute_query(f"DROP TABLE IF EXISTS {schema}.{table_name} CASCADE;")

        log.info("Creating %s table schema if needed...", table_name)
        ddl = f"""
            CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
                id TEXT PRIMARY KEY,
                x_mp INTEGER,
                y_mp INTEGER,
                name TEXT,
                resolution_meters INTEGER,
                geom GEOMETRY
            );
            CREATE INDEX IF NOT EXISTS {table_name}_geom_idx
            ON {schema}.{table_name} USING GIST (geom);
            CREATE INDEX IF NOT EXISTS {table_name}_resolution_idx
            ON {schema}.{table_name} (resolution_meters);
            CREATE INDEX IF NOT EXISTS {table_name}_x_mp_y_mp_idx
            ON {schema}.{table_name} (x_mp, y_mp);
            CREATE INDEX IF NOT EXISTS {table_name}_name_idx
            ON {schema}.{table_name} (name);
        """
        db.execute_query(ddl)

        utils.materialize_scope_table(infdb)  # Ensure opendata.scope exists
        all_envelops = utils.get_envelop(infdb)

        if all_envelops is None or all_envelops.empty:
            log.warning("No scope envelopes found; skipping geogitter creation.")
            return

        for _, envelop in all_envelops.groupby("ags", sort=False):
            log.debug("Envelop: %s", envelop)

            wkt = envelop.to_crs(3035).unary_union.wkt  # Use LAEA (EPSG:3035) for grid generation

            # Ensure list
            if isinstance(resolutions, str):
                resolutions = [resolutions]

            ags_col = "AGS" if "AGS" in envelop.columns else "ags"
            gen_col = "GEN" if "GEN" in envelop.columns else ("gen" if "gen" in envelop.columns else None)

            ags_val = str(envelop[ags_col].iloc[0])
            gen_val = str(envelop[gen_col].iloc[0]) if gen_col else ""

            # Insert per resolution, skipping existing ids
            for resolution in resolutions or []:
                if resolution.endswith("km"):
                    resolution_meters = int(resolution[:-2]) * 1000
                elif resolution.endswith("m"):
                    resolution_meters = int(resolution[:-1])
                else:
                    log.warning("Skipping resolution with unknown unit: %s", resolution)
                    continue

                log.info(
                    "Generating grid cells for %s (%s) with resolution %s",
                    ags_val,
                    gen_val,
                    resolution_meters,
                )
                # todo: add_AGS parameter to identify the area from envelop

                generate_grid_cells_sql = f"""
                    WITH params AS (
                        SELECT {resolution_meters}::int AS cell_size
                    ),
                    boundary AS (
                        SELECT ST_GeomFromText('{wkt}', 3035) AS geom
                    ),
                    envelope AS (
                        SELECT
                            FLOOR(ST_XMin(b.geom) / p.cell_size) * p.cell_size AS x_min,
                            FLOOR(ST_YMin(b.geom) / p.cell_size) * p.cell_size AS y_min,
                            CEIL(ST_XMax(b.geom) / p.cell_size) * p.cell_size AS x_max,
                            CEIL(ST_YMax(b.geom) / p.cell_size) * p.cell_size AS y_max,
                            p.cell_size
                        FROM boundary b, params p
                    ),
                    grid_raw AS (
                        SELECT (ST_SquareGrid(
                                e.cell_size,
                                ST_MakeEnvelope(e.x_min, e.y_min, e.x_max, e.y_max, 3035)
                                )).*
                        FROM envelope e
                    ),
                    grid_filtered AS (
                        SELECT gr.geom
                        FROM grid_raw gr
                        CROSS JOIN boundary b
                        WHERE ST_Covers(b.geom, ST_PointOnSurface(gr.geom))
                    ),
                    grid AS (
                        SELECT
                            ST_Transform(geom, {epsg}) AS geom,
                            ST_XMin(geom) AS x,
                            ST_YMin(geom) AS y
                        FROM grid_filtered
                    ),
                    id_named AS (
                        SELECT
                            FORMAT('%sN%sE%s', '{resolution}', g.y::int::text, g.x::int::text) AS id,
                            (g.x + (p.cell_size / 2.0))::int AS x_mp,
                            (g.y + (p.cell_size / 2.0))::int AS y_mp,
                            'DE_Grid_ETRS89_LAEA_{resolution}'::text AS name,
                            p.cell_size::int AS resolution_meters,
                            g.geom
                        FROM grid g, params p
                    )
                    SELECT id, x_mp, y_mp, name, resolution_meters, geom
                    FROM id_named
                """

                insert_sql = f"""
                INSERT INTO {schema}.{table_name} (id, x_mp, y_mp, name, resolution_meters, geom)
                {generate_grid_cells_sql}
                ON CONFLICT (id) DO NOTHING;
                """

                db.execute_query(insert_sql)


def load(infdb: InfDB) -> bool:
    """Downloads BKG sources, imports layers, and generates geogitter grid.

    Behavior preserved:
    - (Optional) feature guard for BKG: left commented as in original.
    - Download/unzip/import NUTS and VG5000 with scope=False.
    - Create schema if missing; then generate geogitter with configured resolutions.
    """
    log = infdb.get_worker_logger()

    if not utils.if_active("bkg", infdb):
        return

    # Paths
    try:
        zip_path = infdb.get_config_path([infdb.get_toolname(), "sources", "bkg", "path", "zip"], type="loader")
        os.makedirs(zip_path, exist_ok=True)
        unzip_path = infdb.get_config_path([infdb.get_toolname(), "sources", "bkg", "path", "unzip"], type="loader")
        os.makedirs(unzip_path, exist_ok=True)

        schema = infdb.get_config_value([infdb.get_toolname(), "sources", "bkg", "schema"])
        prefix = infdb.get_config_value([infdb.get_toolname(), "sources", "bkg", "prefix"])

        # Ensure schema exists via InfdbClient
        with infdb.connect() as db:
            db.execute_query(f"CREATE SCHEMA IF NOT EXISTS {schema};")

        # --- NUTS (download+unzip+import) ---
        log.info("Downloading and unzipping NUTS")
        nuts_url = infdb.get_config_value([infdb.get_toolname(), "sources", "bkg", "nuts", "url"])
        utils.download_files(nuts_url, zip_path, infdb)
        nuts_zip = utils.get_file(zip_path, filename="nuts250", ending=".zip", infdb=infdb)
        utils.unzip(nuts_zip, unzip_path, infdb)

        nuts_layers = infdb.get_config_value([infdb.get_toolname(), "sources", "bkg", "nuts", "layer"])
        nuts_gpkg = utils.get_file(unzip_path, filename="nuts250", ending=".gpkg", infdb=infdb)
        utils.import_layers(nuts_gpkg, nuts_layers, schema, infdb, prefix, scope=False)

        # --- VG5000 (download+unzip+import) ---
        log.info("Downloading and unzipping VG5000")
        vg_url = infdb.get_config_value([infdb.get_toolname(), "sources", "bkg", "vg5000", "url"])
        utils.download_files(vg_url, zip_path, infdb)
        vg_zip = utils.get_file(zip_path, filename="vg5000", ending=".zip", infdb=infdb)
        utils.unzip(vg_zip, unzip_path, infdb)

        vg_layers = infdb.get_config_value([infdb.get_toolname(), "sources", "bkg", "vg5000", "layer"])
        vg_gpkg = utils.get_file(unzip_path, filename="vg5000", ending=".gpkg", infdb=infdb)
        utils.import_layers(vg_gpkg, vg_layers, schema, infdb, prefix, scope=False)

        # --- Geogitter ---
        resolutions = infdb.get_config_value([infdb.get_toolname(), "sources", "bkg", "geogitter", "resolutions"])
        log.info("Creating Geogitter layers resolutions %s", resolutions)
        create_geogitter(resolutions, infdb, clear_existing=True)

        log.info("BKG data loaded successfully")
    except Exception as err:
        log.exception("An error occurred while processing BKG data: %s", str(err))
