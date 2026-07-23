import json
import logging
import multiprocessing as mp
import subprocess
from pathlib import Path
import sys

from pyinfdb import InfDB
from sqlalchemy import text
import shlex

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



def _write_file_list(file_paths: list[Path], list_path: Path) -> None:
    """Write one file path per line for GDAL input_file_list usage."""
    with open(list_path, "w", encoding="utf-8") as f:
        for path in file_paths:
            f.write(f"{path}\n")

def _chunk_list(items: list, batch_size: int) -> list[list]:
    return [
        items[i:i + batch_size]
        for i in range(0, len(items), batch_size)
    ]


def _convert_dgm1_tile_to_cog_worker(
    source_tif_str: str,
    output_tif_str: str,
    target_res: float | None = None,
) -> tuple[bool, str | None, str | None]:
    """Convert one downloaded DGM1 GeoTIFF into a Cloud Optimized GeoTIFF.

    When target_res is set the tile is downsampled on the way in. Source tiles are
    1km wide, so any resolution that divides 1000 keeps the output grid aligned with
    the tile origin and no -tap is needed.
    """
    try:
        source_tif = Path(source_tif_str)
        output_tif = Path(output_tif_str)

        # Reuse an existing persistent COG file on subsequent runs.
        if output_tif.exists() and output_tif.stat().st_size > 0:
            return True, str(output_tif), None

        output_tif.parent.mkdir(parents=True, exist_ok=True)

        if target_res:
            # average, not bilinear: for pure decimation of a terrain model it keeps
            # the mean elevation of the source cells instead of sampling four of them.
            cmd = [
                "gdalwarp",
                "-overwrite",
                "-of",
                "COG",
                "-co",
                "COMPRESS=ZSTD",
                "-co",
                "BLOCKSIZE=512",
                "-r",
                "average",
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
        else:
            cmd = [
                "gdal_translate",
                "-of",
                "COG",
                "-co",
                "COMPRESS=ZSTD",
                "-co",
                "BLOCKSIZE=512",
                "-a_nodata",
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
            return False, None, f"{cmd[0]} failed for {source_tif}: {proc.stdout}"

        if not output_tif.exists() or output_tif.stat().st_size == 0:
            output_tif.unlink(missing_ok=True)
            return False, None, f"COG output is empty for {source_tif}"

        return True, str(output_tif), None

    except Exception as err:
        return False, None, str(err)


def _convert_dgm1_batch_to_cogs(
    batch: list[str],
    cog_dir_str: str,
    batch_idx: int,
    total_batches: int,
    target_res: float | None = None,
) -> tuple[bool, list[str], list[str], int, int]:
    cog_paths: list[str] = []
    errors: list[str] = []

    cog_dir = Path(cog_dir_str)

    for source_tif_str in batch:
        source_tif = Path(source_tif_str)
        output_tif = cog_dir / source_tif.name

        ok, cog_path, error = _convert_dgm1_tile_to_cog_worker(
            source_tif_str=str(source_tif),
            output_tif_str=str(output_tif),
            target_res=target_res,
        )

        if ok and cog_path:
            cog_paths.append(cog_path)
        else:
            errors.append(error or f"Unknown error for {source_tif}")

    return len(errors) == 0, cog_paths, errors, batch_idx, total_batches


def _convert_dgm1_batch_to_cogs_star(args):
    return _convert_dgm1_batch_to_cogs(*args)


def _convert_dgm1_tiles_to_cogs_in_parallel(
    infdb: InfDB,
    tile_paths: list[Path],
    cog_dir: Path,
    batch_size: int = 200,
    processes: int | None = None,
    target_res: float | None = None,
) -> list[Path]:
    """Convert selected DGM1 tiles into persistent COG files in parallel."""
    log = infdb.get_worker_logger()

    if not tile_paths:
        return []

    batches = _chunk_list([str(p) for p in tile_paths], batch_size)
    total_batches = len(batches)

    if processes is None:
        processes = utils.get_number_processes(infdb)

    processes = max(1, min(processes, total_batches))

    log.info(
        "DGM1 COG: converting %d tiles in %d batches with %d worker(s).",
        len(tile_paths),
        total_batches,
        processes,
    )

    worker_args = [
        (
            batch,
            str(cog_dir),
            i + 1,
            total_batches,
            target_res,
        )
        for i, batch in enumerate(batches)
    ]

    cog_paths: list[Path] = []
    errors: list[str] = []
    completed_batches = 0

    with mp.Pool(processes=processes) as pool:
        for ok, batch_paths, batch_errors, batch_idx, total in pool.imap_unordered(
            _convert_dgm1_batch_to_cogs_star,
            worker_args,
        ):
            completed_batches += 1

            log.info(
                "DGM1 COG: %d/%d batches are completed. Finished batch %d/%d with %d output file(s).",
                completed_batches,
                total,
                batch_idx,
                total,
                len(batch_paths),
            )

            cog_paths.extend(Path(p) for p in batch_paths)

            if not ok:
                errors.extend(batch_errors)

    if errors:
        raise RuntimeError(
            f"DGM1 COG: {len(errors)} tile(s) failed during conversion. First error: {errors[0]}"
        )

    return sorted(set(cog_paths))


def _build_consolidated_overview(
    infdb: InfDB,
    vrt_path: Path,
    output_path: Path,
    overview_res: float,
) -> Path | None:
    """Build one consolidated low-resolution COG covering the whole scope.

    QGIS cannot render the full-resolution mosaic when zoomed out, and the internal
    overviews of the individual COG tiles do not help: at that zoom the cost is
    opening every source tile, not reading pixels. Collapsing the mosaic into a
    single coarse file removes that cost. Measured on the Neuburg/Munich scope
    (488 tiles): full-extent read drops from ~2500 ms to ~50 ms.

    The COG driver adds further internal overview levels on top of this file, so one
    consolidated level is enough to cover the whole zoom range.
    """
    log = infdb.get_worker_logger()

    output_path.unlink(missing_ok=True)

    rc = utils.do_cmd(
        infdb,
        [
            "gdalwarp",
            "-overwrite",
            "-of",
            "COG",
            "-co",
            "COMPRESS=ZSTD",
            "-co",
            "BLOCKSIZE=512",
            "-r",
            "average",
            "-tr",
            str(overview_res),
            str(overview_res),
            "-srcnodata",
            "-9999",
            "-dstnodata",
            "-9999",
            "-multi",
            "-wo",
            "NUM_THREADS=ALL_CPUS",
            str(vrt_path),
            str(output_path),
        ],
    )

    if rc != 0:
        log.error("DGM1 COG OUTDB: consolidated overview generation failed.")
        return None

    if not output_path.exists() or output_path.stat().st_size == 0:
        log.warning("DGM1 COG OUTDB: consolidated overview is empty.")
        return None

    return output_path


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
# COG VERSION: download selected tiles, convert them to COGs, register them out-of-db
# ====================================================================================




def _load_dgm1(infdb: InfDB, base_path: Path, target_epsg: int):
    """Load Bavaria DGM1 as persistent COG files registered out-of-db in PostGIS.

    Workflow:
      * resolve required DGM1 tile URLs for the active scopes
      * select downloaded TIFF files belonging to the current URL list
      * convert each selected TIFF to a persistent COG file
      * reuse existing non-empty COG files on subsequent runs
      * build one persistent VRT from the current scope's COG files for direct QGIS use
      * register only the current scope's COG files directly with raster2pgsql -R
      * create no PostGIS overview tables
      * validate the main out-of-db raster table
    """

    log = infdb.get_worker_logger()

    # ---------- 1. Read configuration ----------
    source_cfg = [infdb.get_toolname(), "sources", "opendata_bavaria"]
    dgm1_cfg = source_cfg + ["datasets", "gelaendemodell_1m"]

    schema = infdb.get_config_value(source_cfg + ["schema"])
    table_base = infdb.get_config_value(dgm1_cfg + ["table_name"])
    source_srid = int(infdb.get_config_value(dgm1_cfg + ["srid"]))
    overview_res = float(infdb.get_config_value(dgm1_cfg + ["overview_resolution"]) or 32.0)

    # Unset (or 1m) means: keep the native DGM1 resolution and skip resampling.
    configured_res = infdb.get_config_value(dgm1_cfg + ["target_resolution"])
    target_res = float(configured_res) if configured_res else None
    if target_res == 1.0:
        target_res = None

    log.info(
        "DGM1 COG OUTDB: schema=%s table=%s srid=%s target_res=%s overview_res=%.1f",
        schema,
        table_base,
        source_srid,
        f"{target_res:g}m" if target_res else "native 1m",
        overview_res,
    )

    # ---------- 2. Working directories ----------
    dgm1_base_dir = base_path / "gelaendemodell_1m"
    dgm1_base_dir.mkdir(parents=True, exist_ok=True)

    # Persistent COG files remain available because PostGIS stores their paths.
    # The resolution is part of the directory name: the worker reuses any existing
    # output file, so a shared directory would silently mix resolutions across runs.
    cog_dir = dgm1_base_dir / (f"cogs_{target_res:g}m" if target_res else "cogs")
    cog_dir.mkdir(parents=True, exist_ok=True)

    # ---------- 3. Read tiled download config ----------
    dgm1_region_cfg = {
        "status": infdb.get_config_value(dgm1_cfg + ["status"]),
        "state_prefix": infdb.get_config_value(dgm1_cfg + ["state_prefix"]),
        "base_url": infdb.get_config_value(dgm1_cfg + ["base_url"]),
        "tile_size_m": infdb.get_config_value(dgm1_cfg + ["tile_size_m"]),
        "filename_template": infdb.get_config_value(dgm1_cfg + ["filename_template"]),
    }

    # ---------- 4. Resolve all intersecting DGM1 tile URLs ----------
    urls = _build_urls_for_region("DGM1 Bavaria", dgm1_region_cfg, infdb, log)

    if not urls:
        log.warning("DGM1 COG OUTDB: no Bavaria tiles resolved for the active scopes; skipping.")
        return

    urls = sorted(set(urls))
    log.info("DGM1 COG OUTDB: %d unique tiles resolved.", len(urls))

    # ---------- 5. Download all tiles once ----------
    utils.download_aria2c_many(infdb, urls, output_dir=str(dgm1_base_dir))

    # ---------- 6. Collect only downloaded TIFF tiles from current URL list ----------
    tile_paths: list[Path] = []
    missing_tile_paths: list[Path] = []

    for url in urls:
        tile_path = dgm1_base_dir / Path(url).name

        if tile_path.exists() and tile_path.is_file() and tile_path.suffix.lower() in [".tif", ".tiff"]:
            tile_paths.append(tile_path)
        else:
            missing_tile_paths.append(tile_path)

    tile_paths = sorted(set(tile_paths))

    if missing_tile_paths:
        # Grid cells that touch the state boundary but hold no data are expected
        # to be absent, so a missing tile must not abort the run.
        log.warning(
            "DGM1 COG OUTDB: %d expected TIFF files are missing. First missing file: %s",
            len(missing_tile_paths),
            missing_tile_paths[0],
        )

    if not tile_paths:
        log.warning("DGM1 COG OUTDB: no expected .tif files found; skipping.")
        return

    log.info("DGM1 COG OUTDB: %d raster tiles selected for COG conversion.", len(tile_paths))

    # ---------- 7. Convert selected TIFF files to persistent COG files ----------
    cog_paths = _convert_dgm1_tiles_to_cogs_in_parallel(
        infdb=infdb,
        tile_paths=tile_paths,
        cog_dir=cog_dir,
        batch_size=200,
        processes=utils.get_number_processes(infdb),
        target_res=target_res,
    )

    if not cog_paths:
        log.warning("DGM1 COG OUTDB: no COG files created; skipping import.")
        return

    # cog_paths contains only files corresponding to URLs resolved for the active scopes.
    # Older COG files from previous scopes may remain in cog_dir, but they are not imported.
    cog_paths = sorted(set(cog_paths))
    log.info("DGM1 COG OUTDB: %d COG files selected for registration.", len(cog_paths))

    try:
        size_mb = sum(p.stat().st_size for p in cog_paths) / 1_000_000
        log.info("DGM1 COG OUTDB: selected COG data size %.1f MB", size_mb)
    except FileNotFoundError:
        log.error("DGM1 COG OUTDB: one or more selected COG files are missing.")
        return

    # ---------- 8. Build a persistent scope-specific VRT for direct QGIS use ----------
    file_list_path = dgm1_base_dir / "dgm1_scope_cog_files.txt"
    vrt_path = dgm1_base_dir / "dgm1_scope_cogs.vrt"

    _write_file_list(cog_paths, file_list_path)

    rc = utils.do_cmd(
        infdb,
        [
            "gdalbuildvrt",
            "-overwrite",
            "-srcnodata",
            "-9999",
            "-vrtnodata",
            "-9999",
            "-input_file_list",
            str(file_list_path),
            str(vrt_path),
        ],
    )

    if rc != 0:
        raise RuntimeError("DGM1 COG OUTDB: failed to build VRT from selected COG files.")

    if not vrt_path.exists() or vrt_path.stat().st_size == 0:
        raise RuntimeError("DGM1 COG OUTDB: generated VRT is empty.")

    log.info("DGM1 COG OUTDB: persistent QGIS VRT created: %s", vrt_path)

    # ---------- 8b. Build the consolidated overview used for zoomed-out rendering ----------
    overview_path = dgm1_base_dir / f"dgm1_overview_{overview_res:g}m.tif"

    log.info(
        "DGM1 COG OUTDB: building consolidated %.1fm overview from %d COG files.",
        overview_res,
        len(cog_paths),
    )

    overview_path = _build_consolidated_overview(
        infdb=infdb,
        vrt_path=vrt_path,
        output_path=overview_path,
        overview_res=overview_res,
    )

    if overview_path:
        log.info(
            "DGM1 COG OUTDB: consolidated overview created: %s (%.1f MB)",
            overview_path,
            overview_path.stat().st_size / 1_000_000,
        )
        log.info(
            "DGM1 COG OUTDB: add this file to QGIS as the zoomed-out layer; "
            "use the full-resolution mosaic only below a scale threshold."
        )
    else:
        log.warning(
            "DGM1 COG OUTDB: no consolidated overview available; "
            "zoomed-out QGIS rendering will be slow."
        )

    # ---------- 9. Drop the previous table and legacy overview tables ----------
    target_table = f"{schema}.{table_base}"

    with infdb.connect() as db:
        db.execute_query(f"DROP TABLE IF EXISTS {target_table} CASCADE;")

        # Remove overview tables left behind by the previous VRT-based implementation.
        # The new COG implementation does not create overview tables.
        for factor in (4, 8, 16):
            db.execute_query(
                f"DROP TABLE IF EXISTS {schema}.o_{factor}_{table_base} CASCADE;"
            )

    # ---------- 10. Register selected COG files directly as out-of-db rasters ----------
    pgurl = utils._pg_connstring_for_psql(infdb)
    psql_cmd = f'psql --no-psqlrc -q -v ON_ERROR_STOP=1 -X "{pgurl}"'

    # All paths cannot go on one command line: statewide Bavaria is ~70k tiles, which
    # is ~5.5 MB of arguments against an ARG_MAX of 2 MB. Register in chunks instead,
    # and add index/constraints once at the end rather than per chunk.
    registration_chunk_size = 500
    path_chunks = _chunk_list(cog_paths, registration_chunk_size)

    log.info(
        "DGM1 COG OUTDB: registering %d COG files with raster2pgsql -R into %s in %d chunk(s).",
        len(cog_paths),
        target_table,
        len(path_chunks),
    )

    for chunk_idx, chunk in enumerate(path_chunks, start=1):
        quoted_cog_paths = " ".join(shlex.quote(str(path)) for path in chunk)
        append_flag = "" if chunk_idx == 1 else "-a "

        import_pipeline = (
            f"raster2pgsql "
            f"-q "
            f"-s {source_srid} "
            f"-R "
            f"-F "
            f"{append_flag}"
            f"-t auto "
            f"-N -9999 "
            f"{quoted_cog_paths} "
            f"{target_table} | {psql_cmd}"
        )

        rc = utils.do_cmd(infdb, import_pipeline, shell=True)

        if rc != 0:
            raise RuntimeError(
                f"DGM1 COG OUTDB: raster2pgsql -R import failed for chunk "
                f"{chunk_idx}/{len(path_chunks)}."
            )

        if chunk_idx % 10 == 0 or chunk_idx == len(path_chunks):
            log.info(
                "DGM1 COG OUTDB: registered %d/%d chunks.",
                chunk_idx,
                len(path_chunks),
            )

    finalize_sql = f"""
        SELECT AddRasterConstraints('{schema}'::name, '{table_base}'::name, 'rast'::name);

        CREATE INDEX IF NOT EXISTS {table_base}_rast_gix
        ON {target_table}
        USING GIST (ST_ConvexHull(rast));

        ANALYZE {target_table};
    """

    rc = utils.do_cmd(infdb, f'{psql_cmd} -c "{finalize_sql}"', shell=True)

    if rc != 0:
        raise RuntimeError("DGM1 COG OUTDB: constraint/index creation failed.")

    log.info("DGM1 COG OUTDB: direct raster2pgsql -R import finished.")

    # ---------- 11. Validate raster metadata ----------
    metadata_sql = f"""
        SELECT
            r_table_name,
            srid,
            scale_x,
            scale_y,
            blocksize_x,
            blocksize_y,
            same_alignment,
            regular_blocking,
            num_bands,
            pixel_types,
            nodata_values,
            out_db
        FROM raster_columns
        WHERE r_table_schema = '{schema}'
          AND r_table_name = '{table_base}';
    """

    log.info("DGM1 COG OUTDB: checking raster_columns metadata for the main table.")
    rc = utils.do_cmd(
        infdb,
        f'{psql_cmd} -c "{metadata_sql}"',
        shell=True,
    )

    if rc != 0:
        raise RuntimeError("DGM1 COG OUTDB: raster_columns metadata query failed.")

    # ---------- 12. Validate that PostgreSQL can read the COG rasters ----------
    read_validation_sql = f"""
        SELECT
            COUNT(*) AS raster_count,
            MIN(ST_Width(rast)) AS min_width,
            MAX(ST_Width(rast)) AS max_width,
            MIN(ST_Height(rast)) AS min_height,
            MAX(ST_Height(rast)) AS max_height,
            MIN(ST_ScaleX(rast)) AS min_scalex,
            MAX(ST_ScaleX(rast)) AS max_scalex,
            MIN(ST_ScaleY(rast)) AS min_scaley,
            MAX(ST_ScaleY(rast)) AS max_scaley,
            SUM(ST_Count(rast, 1, TRUE)) AS valid_pixels
        FROM {target_table};
    """

    log.info("DGM1 COG OUTDB: validating that PostgreSQL can read the registered COG rasters.")
    rc = utils.do_cmd(
        infdb,
        f'{psql_cmd} -c "{read_validation_sql}"',
        shell=True,
    )

    if rc != 0:
        raise RuntimeError(
            "DGM1 COG OUTDB: PostgreSQL could not read the registered out-of-db COG rasters. "
            "Check that the DB container can read the COG paths and that out-db raster access is enabled."
        )

    log.info("DGM1 COG OUTDB: PostgreSQL successfully read the registered COG rasters.")

    # ---------- 13. Show the first few registered COG paths ----------
    path_check_sql = f"""
        SELECT
            rid,
            filename,
            ST_BandPath(rast, 1) AS registered_path,
            ST_Width(rast) AS width,
            ST_Height(rast) AS height,
            ST_ScaleX(rast) AS scalex,
            ST_ScaleY(rast) AS scaley
        FROM {target_table}
        ORDER BY rid
        LIMIT 10;
    """

    log.info("DGM1 COG OUTDB: checking the first registered COG paths.")
    rc = utils.do_cmd(
        infdb,
        f'{psql_cmd} -c "{path_check_sql}"',
        shell=True,
    )

    if rc != 0:
        log.warning("DGM1 COG OUTDB: could not inspect registered COG paths.")

    log.info("DGM1 COG OUTDB: COG-based out-of-db import finished successfully.")


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