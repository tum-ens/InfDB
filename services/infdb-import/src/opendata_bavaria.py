import json
import logging
import multiprocessing as mp
import os
import subprocess
from pathlib import Path
from typing import Dict, List

import geopandas as gpd
from pyinfdb import InfDB
from sqlalchemy import text
from shapely import wkt as shapely_wkt

from . import utils
from .lod2 import _build_urls_for_region

# Module logger
log = logging.getLogger(__name__)


# ====================================================================================
# HELPER FUNCTIONS - Utilities for GDAL/OGR operations and geometry calculations
# ====================================================================================


def _get_gpkg_layers(gpkg: Path) -> list[str]:
    """Lists layer names in a GPKG."""
    try:
        # Attempt JSON parsing (preferred method for structured output)
        out = subprocess.check_output(["ogrinfo", "-ro", "-q", "-json", str(gpkg)], text=True)
        data = json.loads(out)
        return [lyr.get("name") for lyr in data.get("layers", []) if "name" in lyr]
    except Exception:
        # Fallback: parse text output line by line
        # Expected format: "1: layer_name (Geometry Type)"
        out = subprocess.check_output(["ogrinfo", "-ro", "-q", str(gpkg)], text=True, stderr=subprocess.STDOUT)
        return [line.split(":", 1)[1].split("(")[0].strip() for line in out.splitlines() if ":" in line and "(" in line]


def _urls_to_local_paths(
    urls: list[str],
    base_dir: str | Path,
    log,
    *,
    expected_suffix: str | None = None,
) -> list[str]:
    """Resolve current-run URLs to existing local file paths in base_dir."""
    base_dir = str(base_dir)
    local_files = []
    missing_files = []

    for url in urls:
        filename = os.path.basename(url)
        local_path = os.path.join(base_dir, filename)

        if expected_suffix and not filename.lower().endswith(expected_suffix.lower()):
            log.warning("Skipping unexpected file extension for URL: %s", url)
            continue

        if os.path.isfile(local_path):
            local_files.append(local_path)
        else:
            missing_files.append(local_path)

    if missing_files:
        log.warning("Expected %d downloaded files are missing locally.", len(missing_files))
        for path in missing_files[:20]:
            log.warning("Missing file: %s", path)
        if len(missing_files) > 20:
            log.warning("... and %d more missing files.", len(missing_files) - 20)

    return sorted(set(local_files))


def _chunk_list(items: list[str], chunk_size: int) -> list[list[str]]:
    """Split items into fixed-size chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def _write_file_list(file_paths: list[str], list_path: Path) -> None:
    """Write one file path per line for GDAL input_file_list usage."""
    with open(list_path, "w", encoding="utf-8") as f:
        for path in file_paths:
            f.write(f"{path}\n")


def _cleanup_paths(paths: list[Path], log) -> None:
    """Delete generated helper/output files if they exist."""
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            log.warning("Could not remove temporary file: %s", path)


def _process_dgm1_batch_and_append(
    batch_files: list[str],
    tool_name: str,
    source_srid: int,
    target_res: float,
    target_table: str,
    mask_path_str: str,
    work_dir: str,
    batch_index: int,
    total_batches: int,
) -> bool:
    try:
        infdb = InfDB(tool_name=tool_name, config_path="../configs/config-infdb-import.yml")
        log = infdb.get_worker_logger()

        if not batch_files:
            log.info("DGM1 batch %d/%d: empty batch, skipping.", batch_index, total_batches)
            return True

        work_dir = Path(work_dir)
        mask_path = Path(mask_path_str)

        file_list_path = work_dir / f"dgm1_batch_{batch_index:04d}.txt"
        vrt_path = work_dir / f"dgm1_batch_{batch_index:04d}.vrt"
        clipped_tif = work_dir / f"dgm1_batch_{batch_index:04d}.tif"

        _write_file_list(batch_files, file_list_path)

        rc = utils.do_cmd(
            infdb,
            [
                "gdalbuildvrt",
                "-input_file_list",
                str(file_list_path),
                str(vrt_path),
            ],
        )
        if rc != 0:
            log.error("DGM1 batch %d/%d: gdalbuildvrt failed.", batch_index, total_batches)
            return False

        rc = utils.do_cmd(
            infdb,
            [
                "gdalwarp",
                "-overwrite",
                "-of",
                "GTiff",
                "-co",
                "TILED=YES",
                "-co",
                "COMPRESS=DEFLATE",
                "-co",
                "PREDICTOR=2",
                "-co",
                "BIGTIFF=IF_SAFER",
                "-co",
                "BLOCKXSIZE=512",
                "-co",
                "BLOCKYSIZE=512",
                "-r",
                "bilinear",
                "-multi",
                "-wo",
                "NUM_THREADS=ALL_CPUS",
                "-t_srs",
                f"EPSG:{source_srid}",
                "-tr",
                str(target_res),
                str(target_res),
                "-srcnodata",
                "-9999",
                "-dstnodata",
                "-9999",
                "-cutline",
                str(mask_path),
                "-cl",
                "mask",
                "-crop_to_cutline",
                str(vrt_path),
                str(clipped_tif),
            ],
        )
        if rc != 0:
            log.error("DGM1 batch %d/%d: gdalwarp failed.", batch_index, total_batches)
            return False

        if not clipped_tif.exists() or clipped_tif.stat().st_size == 0:
            log.warning("DGM1 batch %d/%d: clipped TIFF is empty, skipping append.", batch_index, total_batches)
            return True

        pgurl = utils._pg_connstring_for_psql(infdb)
        psql_cmd = f'psql --no-psqlrc -q -v ON_ERROR_STOP=1 -X "{pgurl}"'

        import_pipeline = (
            f'raster2pgsql -q -a -s {source_srid} -N -9999 -t 100x100 "{clipped_tif}" {target_table} | {psql_cmd}'
        )

        rc = utils.do_cmd(infdb, import_pipeline, shell=True)
        if rc != 0:
            log.error("DGM1 batch %d/%d: raster2pgsql append failed.", batch_index, total_batches)
            return False

        return True

    except Exception:
        if "log" in locals():
            log.exception("DGM1 batch %d/%d failed unexpectedly.", batch_index, total_batches)
        return False


def _append_dgm1_batches_in_parallel(
    infdb: InfDB,
    tile_paths: list[str],
    source_srid: int,
    target_res: float,
    target_table: str,
    mask_path: Path,
    work_dir: str | Path,
    batch_size: int = 200,
    processes: int | None = None,
) -> None:
    log = infdb.get_worker_logger()

    if not tile_paths:
        log.warning("DGM1: no TIFF tiles to process.")
        return

    batches = _chunk_list(tile_paths, batch_size)
    total_batches = len(batches)

    if processes is None:
        processes = utils.get_number_processes(infdb)

    processes = max(1, min(processes, total_batches))

    with mp.Pool(processes=processes) as pool:
        results = pool.starmap(
            _process_dgm1_batch_and_append,
            [
                (
                    batch,
                    infdb.get_toolname(),
                    source_srid,
                    target_res,
                    target_table,
                    str(mask_path),
                    str(work_dir),
                    i + 1,
                    total_batches,
                )
                for i, batch in enumerate(batches)
            ],
        )

    if not all(results):
        raise RuntimeError("DGM1: one or more batch append jobs failed.")


def _finalize_dgm1_raster_table(infdb: InfDB, target_table: str) -> None:
    """Finalize raster table after parallel appends without using AddRasterConstraints."""
    table_name = target_table.split(".", 1)[1]
    index_name = f"{table_name}_st_convexhull_idx"

    with infdb.connect() as db:
        db.execute_query(
            f"CREATE INDEX IF NOT EXISTS {index_name} "
            f"ON {target_table} USING GIST (ST_ConvexHull(rast));"
        )
        db.execute_query(f"ANALYZE {target_table};")


# ====================================================================================
# MAIN ORCHESTRATION - Entry point that coordinates all dataset loaders
# ====================================================================================


def load(infdb: InfDB) -> bool:
    """Main entry point for loading OpenData Bavaria datasets."""
    try:
        log = infdb.get_worker_logger()

        # Early exit if this module is disabled
        if not utils.if_active("opendata_bavaria", infdb):
            return True

        # -------------------- Enable PostGIS Extensions --------------------
        # PostGIS raster needed for DGM1 elevation data
        with infdb.connect() as db:
            db.execute_query("CREATE EXTENSION IF NOT EXISTS postgis_raster SCHEMA public CASCADE;")
            log.info("PostGIS raster extension enabled")

        # -------------------- Configuration Setup --------------------
        # Get base directory for downloaded/processed files
        base_path = Path(
            infdb.get_config_path(
                [infdb.get_toolname(), "sources", "opendata_bavaria", "path", "base"],
                type="loader",
            )
        )
        base_path.mkdir(parents=True, exist_ok=True)

        # Read dataset configurations
        datasets = infdb.get_config_value([infdb.get_toolname(), "sources", "opendata_bavaria", "datasets"]) or {}

        # -------------------- Database Connection Parameters --------------------
        db_params = infdb.get_db_parameters_dict()
        pgurl = (
            f"postgresql://{db_params['user']}:{db_params['password']}"
            f"@{db_params['host']}:{db_params['exposed_port']}/{db_params['db']}"
        )
        target_epsg = db_params["epsg"]

        # -------------------- Load DGM1 (Digital Terrain Model) --------------------
        dgm1_cfg = datasets.get("gelaendemodell_1m", {})
        if dgm1_cfg.get("status") == "active":
            _load_dgm1(infdb, base_path, target_epsg)

        # -------------------- Load TN (Land Use) --------------------
        tn_cfg = datasets.get("tatsaechliche_nutzung", {})
        if tn_cfg.get("status") == "active":
            _load_tatsaechliche_nutzung(infdb, tn_cfg, base_path, pgurl, target_epsg)

        log.info("OpenData Bavaria: complete.")
        return True

    except Exception as err:
        log.exception(f"An error occurred in OpenData Bavaria loader: {str(err)}")
        sys.exit(1)


# ====================================================================================
# DGM1 LOADER - Digital Terrain Model (Elevation Raster Data)
# SIMPLE VERSION: just download all tiles per Landkreis and import into PostGIS
# ====================================================================================


def _load_dgm1(infdb: InfDB, base_path: Path, target_epsg: int):
    """Loads Bavaria DGM1 using tiled statewide download logic.

    Behavior:
      * resolves one Bavaria-scoped geometry via utils.get_clip_geometry(...)
      * computes all intersecting DGM1 tiles using regular grid logic
      * downloads all required tiles once into a shared folder
      * clips them exactly to the configured scope polygon
      * imports the final clipped raster into one target table

    """

    log = infdb.get_worker_logger()

    # ---------- 1. Read configuration ----------
    source_cfg = [infdb.get_toolname(), "sources", "opendata_bavaria"]
    dgm1_cfg = source_cfg + ["datasets", "gelaendemodell_1m"]

    schema = (
        infdb.get_config_value(source_cfg + ["schema"])
    )
    table_base = infdb.get_config_value(dgm1_cfg + ["table_name"])
    source_srid = int(infdb.get_config_value(dgm1_cfg + ["srid"]))
    target_res = float(infdb.get_config_value(dgm1_cfg + ["target_resolution"]) or 1.0)

    log.info(
        "DGM1: schema=%s table=%s srid=%s target_res=%.2f",
        schema,
        table_base,
        source_srid,
        target_res,
    )

    # Shared working directory for all downloaded raw DGM1 tiles
    dgm1_base_dir = base_path / "gelaendemodell_1m"
    dgm1_base_dir.mkdir(parents=True, exist_ok=True)

    # ---------- 2. Read tiled download config ----------
    dgm1_region_cfg = {
        "status": infdb.get_config_value(dgm1_cfg + ["status"]),
        "state_prefix": infdb.get_config_value(dgm1_cfg + ["state_prefix"]),
        "base_url": infdb.get_config_value(dgm1_cfg + ["base_url"]),
        "tile_size_m": infdb.get_config_value(dgm1_cfg + ["tile_size_m"]),
        "filename_template": infdb.get_config_value(dgm1_cfg + ["filename_template"]),
    }

    # ---------- 3. Resolve all intersecting DGM1 tile URLs ----------
    urls = _build_urls_for_region("DGM1 Bavaria", dgm1_region_cfg, infdb, log)

    if not urls:
        log.warning("DGM1: no Bavaria tiles resolved for the active scopes; skipping.")
        return

    log.info("DGM1: %d unique tiles to download.", len(urls))

    # ---------- 4. Download all tiles once ----------
    utils.download_aria2c_many(infdb, urls, output_dir=str(dgm1_base_dir))

    # ---------- 5. Collect all downloaded TIFF tiles ----------
    tile_paths = _urls_to_local_paths(urls, dgm1_base_dir, log, expected_suffix=".tif")

    if not tile_paths:
        log.warning("DGM1: no .tif tiles found after download; skipping.")
        return

    log.info("DGM1: %d raster tiles available for clipping.", len(tile_paths))

    # ---------- 6. Resolve exact clip geometry ----------
    # We clip exactly to the real configured scope, but the tile
    # download step is done once on the statewide grid.
    state_prefix = dgm1_region_cfg.get("state_prefix")
    clip_wkt, _, _ = utils.get_clip_geometry(target_crs=source_srid, infdb=infdb, state_prefix=state_prefix)
    if not clip_wkt:
        log.warning("DGM1: no clip geometry resolved for state prefix %s; skipping.", state_prefix)
        return

    scope_geom = shapely_wkt.loads(clip_wkt)

    # ---------- 7. Write cutline geometry ----------
    mask_path = dgm1_base_dir / "mask_dgm1.gpkg"
    gdf = gpd.GeoDataFrame(
        {"id": [1]},
        geometry=[scope_geom],
        crs=f"EPSG:{source_srid}",
    )
    gdf.to_file(mask_path, layer="mask", driver="GPKG")

    # ---------- 8. Clip / merge all tiles into one raster ----------
    target_table = f"{schema}.{table_base}"
    generated_paths: list[Path] = []

    try:
        batch_size = 200
        batch_processes = 2

        total_batches = len(_chunk_list(tile_paths, batch_size))
        for i in range(1, total_batches + 1):
            generated_paths.extend(
                [
                    dgm1_base_dir / f"dgm1_batch_{i:04d}.txt",
                    dgm1_base_dir / f"dgm1_batch_{i:04d}.vrt",
                    dgm1_base_dir / f"dgm1_batch_{i:04d}.tif",
                ]
            )

        with infdb.connect() as db:
            db.execute_query(f"DROP TABLE IF EXISTS {target_table};")

        pgurl = utils._pg_connstring_for_psql(infdb)
        psql_cmd = f'psql --no-psqlrc -q -v ON_ERROR_STOP=1 -X "{pgurl}"'

        prepare_pipeline = (
            f'raster2pgsql -q -p -s {source_srid} -N -9999 -t 100x100 "{tile_paths[0]}" {target_table} | {psql_cmd}'
        )
        utils.do_cmd(infdb, prepare_pipeline, shell=True)

        log.info("DGM1: starting parallel batch clip + append import into %s", target_table)

        _append_dgm1_batches_in_parallel(
            infdb=infdb,
            tile_paths=tile_paths,
            source_srid=source_srid,
            target_res=target_res,
            target_table=target_table,
            mask_path=mask_path,
            work_dir=dgm1_base_dir,
            batch_size=batch_size,
            processes=batch_processes,
        )

        log.info("DGM1: all batch appends completed. Finalizing raster table.")

        _finalize_dgm1_raster_table(infdb, target_table)

        log.info("DGM1: import finished.")

    finally:
        generated_paths.append(mask_path)
        _cleanup_paths(generated_paths, log)


# ====================================================================================
# LAND USE (TN) LOADER - Vector Polygon Data for Actual Land Usage
# ====================================================================================


def _load_tatsaechliche_nutzung(infdb: InfDB, cfg: dict, base_path: Path, pgurl: str, target_epsg: int):
    """Loads land use (TN) from Nutzung_kreis.gpkg into PostGIS."""

    url = cfg["url"]
    schema = cfg.get("schema", "opendata")
    table = cfg.get("table_name", "tatsaechliche_nutzung")

    tn_dir = base_path / "tatsaechliche_nutzung"
    tn_dir.mkdir(parents=True, exist_ok=True)
    gpkg_path = tn_dir / "Nutzung_kreis.gpkg"

    # ==================== 2. DOWNLOAD GPKG ====================
    # Check if we have a valid cached copy (> 1GB indicates complete download)
    if gpkg_path.exists() and gpkg_path.stat().st_size > 1_000_000_000:
        log.info(f"TN: using existing {gpkg_path.stat().st_size / 1e9:.1f} GB GPKG")
    else:
        log.info(f"TN: downloading TN dataset from {url}")
        utils.download_aria2c(
            infdb=infdb,
            url=url,
            output_dir=tn_dir,
            output_filename="Nutzung_kreis.gpkg",
            connections=4,
            max_connection_per_server=4,
        )

    # ==================== 3. SCHEMA SETUP ====================
    # Ensure target schema exists in database
    engine = infdb.get_db_engine()

    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema};"))
        conn.commit()

    # ==================== 4. SCOPE GEOMETRY CHECK ====================
    # Verify we have a scope polygon for spatial filtering
    clip_wkt, _, _ = utils.get_clip_geometry(target_crs=target_epsg, infdb=infdb, state_prefix="09")
    if not clip_wkt:
        log.warning("TN: No scope geometry found; skipping TN import.")
        return
    else:
        log.info("TN: scope geometry available will use it for spatial filtering via ogr2ogr.")

    # ==================== 5. LAYER DISCOVERY ====================
    # Enumerate all thematic layers in the GeoPackage
    layer_names = _get_gpkg_layers(gpkg_path)
    if not layer_names:
        raise RuntimeError(f"TN: no layers found in {gpkg_path}")

    log.info(f"TN: Nutzung_kreis.gpkg contains {len(layer_names)} layers.")

    # ==================== 6. IMPORT ALL LAYERS INTO ONE TABLE ====================
    # Import all thematic layers from the GeoPackage into a single target table.
    # Spatial filtering by scope is handled inside utils.import_layers.
    log.info(
        "TN: importing all %d layers into %s.%s (clipped to scope)...",
        len(layer_names),
        schema,
        table,
    )

    # Map every source layer name to the same destination table name
    dest_names = [table] * len(layer_names)

    utils.import_layers(
        input_file=str(gpkg_path),
        layers=layer_names,  # all source layers at once
        schema=schema,
        infdb=infdb,
        layer_names=dest_names,  # each layer -> same table
        scope=True,  # apply scope clipping
        overwrite=True,  # overwrite existing table before import
    )
    # ==================== 7. Create Views ====================
    # Create vies for each nutzart to simplify querying. Each view filters the main table for one nutzart.
    nutzart_name_dict = {"und ": "", " ": "_", "-": "", "/": "_", "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", ",": ""}
    
    with engine.connect() as conn:
        nutzarten = conn.execute(text(f"SELECT DISTINCT nutzart FROM {schema}.{table}")).scalars().all()

        for nutzart in nutzarten:
            nutzart_name = nutzart
            for o_word, n_word in nutzart_name_dict.items():
                nutzart_name = nutzart_name.replace(o_word, n_word)
            
            view_name = f"{table}_{nutzart_name}"
            conn.execute(
                text(
                    f"""
                    CREATE OR REPLACE VIEW {schema}.{view_name} AS
                    SELECT *
                    FROM {schema}.{table}
                    WHERE nutzart = '{nutzart}';
                    """
                )
            )
        conn.commit()

    # ==================== 8. FINALIZATION ====================
    # Get final row count and create spatial index if there is data
    total_rows_imported = 0
    with engine.connect() as conn:
        try:
            total_rows_imported = conn.execute(text(f"SELECT COUNT(*) FROM {schema}.{table}")).scalar() or 0
        except Exception:
            total_rows_imported = 0

        if total_rows_imported > 0:
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS {table}_geom_gix ON {schema}.{table} USING GIST(geom);"))
            conn.commit()

    if total_rows_imported > 0:
        log.info(
            "TN: import finished for %s.%s. Total rows after import: %,d.",
            schema,
            table,
            total_rows_imported,
        )
    else:
        log.warning("TN: no TN features were imported into %s.%s.", schema, table)
