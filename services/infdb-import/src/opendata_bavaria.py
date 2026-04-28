import json
import logging
import multiprocessing as mp
import subprocess
from pathlib import Path
from typing import Dict, List
import sys

<<<<<<< HEAD
from pyinfdb import InfDB
from sqlalchemy import text
import shlex
=======
import geopandas as gpd
from infdb import InfDB
from sqlalchemy import text
from shapely import wkt as shapely_wkt
>>>>>>> f30ea441 (resampling logic is parallelized)

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


def _resample_dgm1_tile(
    infdb: InfDB,
    source_tif: Path,
    output_tif: Path,
    source_srid: int,
    target_res: float,
) -> Path | None:
    """Resample one DGM1 tile to the configured target resolution without clipping."""
    log = infdb.get_worker_logger()

    if output_tif.exists() and output_tif.stat().st_size > 0:
        return output_tif

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
            str(source_tif),
            str(output_tif),
        ],
    )

    if rc != 0:
        log.error("DGM1: gdalwarp resampling failed for %s", source_tif)
        return None

    if not output_tif.exists() or output_tif.stat().st_size == 0:
        log.warning("DGM1: resampled TIFF is empty for %s", source_tif)
        return None

    return output_tif


def _chunk_list(items: list, batch_size: int) -> list[list]:
    return [
        items[i:i + batch_size]
        for i in range(0, len(items), batch_size)
    ]


def _resample_dgm1_tile_worker(
    source_tif_str: str,
    output_tif_str: str,
    source_srid: int,
    target_res: float,
) -> tuple[bool, str | None, str | None]:
    try:
        source_tif = Path(source_tif_str)
        output_tif = Path(output_tif_str)

        if output_tif.exists() and output_tif.stat().st_size > 0:
            return True, str(output_tif), None

        output_tif.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
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
            "NUM_THREADS=1",
            "-t_srs",
            f"EPSG:{source_srid}",
            "-tr",
            str(target_res),
            str(target_res),
            "-srcnodata",
            "-9999",
            "-dstnodata",
            "-9999",
            str(source_tif),
            str(output_tif),
        ]

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        if proc.returncode != 0:
            output_tif.unlink(missing_ok=True)
            return False, None, f"gdalwarp failed for {source_tif}: {proc.stdout}"

        if not output_tif.exists() or output_tif.stat().st_size == 0:
            output_tif.unlink(missing_ok=True)
            return False, None, f"resampled TIFF is empty for {source_tif}"

        return True, str(output_tif), None

    except Exception as err:
        return False, None, str(err)


def _resample_dgm1_batch(
    batch: list[str],
    resampled_dir_str: str,
    source_srid: int,
    target_res: float,
    batch_idx: int,
    total_batches: int,
) -> tuple[bool, list[str], list[str], int, int]:
    resampled_paths: list[str] = []
    errors: list[str] = []

    resampled_dir = Path(resampled_dir_str)

    for source_tif_str in batch:
        source_tif = Path(source_tif_str)
        output_tif = resampled_dir / source_tif.name

        ok, resampled_path, error = _resample_dgm1_tile_worker(
            source_tif_str=str(source_tif),
            output_tif_str=str(output_tif),
            source_srid=source_srid,
            target_res=target_res,
        )

        if ok and resampled_path:
            resampled_paths.append(resampled_path)
        else:
            errors.append(error or f"Unknown error for {source_tif}")

    return len(errors) == 0, resampled_paths, errors, batch_idx, total_batches

def _resample_dgm1_batch_star(args):
    return _resample_dgm1_batch(*args)

def _resample_dgm1_tiles_in_parallel(
    infdb: InfDB,
    tile_paths: list[Path],
    resampled_dir: Path,
    source_srid: int,
    target_res: float,
    batch_size: int = 200,
    processes: int | None = None,
) -> list[Path]:
    log = infdb.get_worker_logger()

    if not tile_paths:
        return []

    batches = _chunk_list([str(p) for p in tile_paths], batch_size)
    total_batches = len(batches)

    if processes is None:
        processes = utils.get_number_processes(infdb)

    processes = max(1, min(processes, total_batches))

    log.info(
        "DGM1: resampling %d tiles in %d batches with %d worker(s).",
        len(tile_paths),
        total_batches,
        processes,
    )

    worker_args = [
        (
            batch,
            str(resampled_dir),
            source_srid,
            target_res,
            i + 1,
            total_batches,
        )
        for i, batch in enumerate(batches)
    ]

    resampled_paths: list[Path] = []
    errors: list[str] = []
    completed_batches = 0

    with mp.Pool(processes=processes) as pool:
        for ok, batch_paths, batch_errors, batch_idx, total in pool.imap_unordered(
            _resample_dgm1_batch_star,
            worker_args,
        ):
            completed_batches += 1

            log.info(
                "DGM1: %d/%d batches are completed. Finished batch %d/%d with %d output file(s).",
                completed_batches,
                total,
                batch_idx,
                total,
                len(batch_paths),
            )

            resampled_paths.extend(Path(p) for p in batch_paths)

            if not ok:
                errors.extend(batch_errors)

    if errors:
        raise RuntimeError(
            f"DGM1: {len(errors)} tile(s) failed during parallel resampling. First error: {errors[0]}"
        )

    return sorted(set(resampled_paths))


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
# SIMPLE VERSION: download selected tiles, resample them, build VRT, import into PostGIS
# ====================================================================================


def _load_dgm1(infdb: InfDB, base_path: Path, target_epsg: int):
    """Loads Bavaria DGM1 using tiled statewide download logic.

    Behavior:
      * resolves all required DGM1 tile URLs for the active scopes
      * downloads all required tiles once into a shared folder
      * selects only TIFF files belonging to the current URL list
      * resamples each selected tile to the configured target resolution
      * builds a VRT from the current resampled tiles
      * imports the VRT into one target table

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

    resampled_dir = dgm1_base_dir / f"resampled_{target_res:g}m"
    resampled_dir.mkdir(parents=True, exist_ok=True)

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

    urls = sorted(set(urls))

    log.info("DGM1: %d unique tiles to download.", len(urls))

    # ---------- 4. Download all tiles once ----------
    #utils.download_aria2c_many(infdb, urls, output_dir=str(dgm1_base_dir))

    # ---------- 5. Collect only downloaded TIFF tiles from current URL list ----------
    tile_paths = []
    missing_tile_paths = []

    for url in urls:
        tile_path = dgm1_base_dir / Path(url).name

        if tile_path.exists() and tile_path.is_file() and tile_path.suffix.lower() in [".tif", ".tiff"]:
            tile_paths.append(tile_path)
        else:
            missing_tile_paths.append(tile_path)

    tile_paths = sorted(set(tile_paths))

    if missing_tile_paths:
        log.warning(
            "DGM1: %d expected TIFF files are missing after download. First missing file: %s",
            len(missing_tile_paths),
            missing_tile_paths[0],
        )

    if not tile_paths:
        log.warning("DGM1: no expected .tif tiles found after download; skipping.")
        return

    log.info("DGM1: %d raster tiles selected from current URL list for resampling.", len(tile_paths))

    # ---------- 6. Resample all current tiles to target resolution ----------
    resampled_paths = _resample_dgm1_tiles_in_parallel(
        infdb=infdb,
        tile_paths=tile_paths,
        resampled_dir=resampled_dir,
        source_srid=source_srid,
        target_res=target_res,
        batch_size=200,
        processes=utils.get_number_processes(infdb),
    )

    if not resampled_paths:
        log.warning("DGM1: no resampled TIFF files created; skipping import.")
        return

    log.info("DGM1: %d raster tiles resampled.", len(resampled_paths))

    # ---------- 7. Build VRT from current resampled rasters ----------
    file_list_path = dgm1_base_dir / "dgm1_resampled_files.txt"
    vrt_path = dgm1_base_dir / f"dgm1_{target_res:g}m_resampled.vrt"

    try:
        _write_file_list([str(p) for p in resampled_paths], file_list_path)

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
            raise RuntimeError("DGM1: failed to build VRT from resampled TIFFs.")

        if not vrt_path.exists() or vrt_path.stat().st_size == 0:
            raise RuntimeError("DGM1: generated VRT is empty.")

        log.info("DGM1: created VRT for current resampled rasters: %s", vrt_path)

        # ---------- 8. Validate output ----------
        try:
            size_mb = sum(p.stat().st_size for p in resampled_paths) / 1_000_000
        except FileNotFoundError:
            log.error("DGM1: one or more resampled TIFF files are missing.")
            return

        if size_mb <= 0:
            log.warning("DGM1: resampled raster files are empty; skipping import.")
            return

        log.info("DGM1: current resampled raster data size %.1f MB", size_mb)

        # ---------- 9. Import into PostGIS ----------
        target_table = f"{schema}.{table_base}"

        pgurl = utils._pg_connstring_for_psql(infdb)
        psql_cmd = f'psql --no-psqlrc -q -v ON_ERROR_STOP=1 -X "{pgurl}"'

        import_pipeline = (
            f'raster2pgsql -q -s {source_srid} -I -C -M -N -9999 -t 100x100 -l 4,8,16 "{vrt_path}" {target_table} | {psql_cmd}'
        )

        log.info("DGM1: importing into %s", target_table)
        rc = utils.do_cmd(infdb, import_pipeline, shell=True)

        if rc != 0:
            raise RuntimeError("DGM1: raster2pgsql import failed.")

        log.info("DGM1: import finished.")

    finally:
        _cleanup_paths([file_list_path, vrt_path], log)


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