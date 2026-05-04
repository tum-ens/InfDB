import json
import logging
import multiprocessing as mp
import subprocess
from pathlib import Path
from typing import Dict, List
import sys
import psycopg2

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
            "-tap",
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
            "-tap",
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


def _resample_and_import_dgm1_batch(
    batch: list[str],
    resampled_dir_str: str,
    dgm1_base_dir_str: str,
    source_srid: int,
    target_res: float,
    schema: str,
    table_base: str,
    pgurl: str,
    batch_idx: int,
    total_batches: int,
) -> tuple[bool, str | None, str | None, list[str], int, int]:
    resampled_paths: list[str] = []
    errors: list[str] = []

    resampled_dir = Path(resampled_dir_str)
    dgm1_base_dir = Path(dgm1_base_dir_str)

    stage_tiled_table = f"{schema}.{table_base}_stage_tiled_{batch_idx:04d}"
    stage_untiled_table = f"{schema}.{table_base}_stage_untiled_{batch_idx:04d}"

    file_list_path = dgm1_base_dir / f"dgm1_batch_{batch_idx:04d}_files.txt"
    vrt_path = dgm1_base_dir / f"dgm1_batch_{batch_idx:04d}_{target_res:g}m.vrt"

    try:
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

        if errors:
            return False, None, None, errors, batch_idx, total_batches

        if not resampled_paths:
            return False, None, None, [f"No resampled paths for batch {batch_idx}"], batch_idx, total_batches

        _write_file_list(resampled_paths, file_list_path)

        proc = subprocess.run(
            [
                "gdalbuildvrt",
                "-srcnodata",
                "-9999",
                "-vrtnodata",
                "-9999",
                "-input_file_list",
                str(file_list_path),
                str(vrt_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        if proc.returncode != 0:
            return False, None, None, [f"gdalbuildvrt failed for batch {batch_idx}: {proc.stdout}"], batch_idx, total_batches

        if not vrt_path.exists() or vrt_path.stat().st_size == 0:
            return False, None, None, [f"generated VRT is empty for batch {batch_idx}"], batch_idx, total_batches

        psql_cmd = f'psql --no-psqlrc -q -v ON_ERROR_STOP=1 -X "{pgurl}"'

        for stage_table in [stage_tiled_table, stage_untiled_table]:
            drop_stage_cmd = f'{psql_cmd} -c "DROP TABLE IF EXISTS {stage_table} CASCADE;"'

            proc = subprocess.run(
                drop_stage_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            if proc.returncode != 0:
                return False, None, None, [f"failed to drop stage table {stage_table}: {proc.stdout}"], batch_idx, total_batches

        tiled_import_pipeline = (
            f'raster2pgsql '
            f'-q '
            f'-s {source_srid} '
            f'-I '
            f'-C '
            f'-M '
            f'-N -9999 '
            f'-t 100x100 '
            f'"{vrt_path}" '
            f'{stage_tiled_table} | {psql_cmd}'
        )

        proc = subprocess.run(
            tiled_import_pipeline,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        if proc.returncode != 0:
            return False, None, None, [f"tiled raster2pgsql failed for batch {batch_idx}: {proc.stdout}"], batch_idx, total_batches

        untiled_import_pipeline = (
            f'raster2pgsql '
            f'-q '
            f'-s {source_srid} '
            f'-I '
            f'-C '
            f'-M '
            f'-N -9999 '
            f'"{vrt_path}" '
            f'{stage_untiled_table} | {psql_cmd}'
        )

        proc = subprocess.run(
            untiled_import_pipeline,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        if proc.returncode != 0:
            return False, None, None, [f"untiled raster2pgsql failed for batch {batch_idx}: {proc.stdout}"], batch_idx, total_batches

        return True, stage_tiled_table, stage_untiled_table, [], batch_idx, total_batches

    except Exception as err:
        return False, None, None, [str(err)], batch_idx, total_batches

    finally:
        try:
            file_list_path.unlink(missing_ok=True)
        except Exception:
            pass

        try:
            vrt_path.unlink(missing_ok=True)
        except Exception:
            pass


def _resample_and_import_dgm1_batch_star(args):
    return _resample_and_import_dgm1_batch(*args)


def _resample_and_import_dgm1_batches_in_parallel(
    infdb: InfDB,
    tile_paths: list[Path],
    resampled_dir: Path,
    dgm1_base_dir: Path,
    source_srid: int,
    target_res: float,
    schema: str,
    table_base: str,
    batch_size: int = 200,
    processes: int | None = None,
) -> tuple[list[str], list[str]]:
    log = infdb.get_worker_logger()

    if not tile_paths:
        return [], []

    pgurl = utils._pg_connstring_for_psql(infdb)

    batches = _chunk_list([str(p) for p in tile_paths], batch_size)
    total_batches = len(batches)

    if processes is None:
        processes = utils.get_number_processes(infdb)

    processes = max(1, min(processes, total_batches))

    log.info(
        "DGM1: resampling and importing %d tiles in %d batches with %d worker(s).",
        len(tile_paths),
        total_batches,
        processes,
    )

    worker_args = [
        (
            batch,
            str(resampled_dir),
            str(dgm1_base_dir),
            source_srid,
            target_res,
            schema,
            table_base,
            pgurl,
            i + 1,
            total_batches,
        )
        for i, batch in enumerate(batches)
    ]

    stage_tiled_tables: list[str] = []
    stage_untiled_tables: list[str] = []
    errors: list[str] = []
    completed_batches = 0

    with mp.Pool(processes=processes) as pool:
        for ok, stage_tiled_table, stage_untiled_table, batch_errors, batch_idx, total in pool.imap_unordered(
            _resample_and_import_dgm1_batch_star,
            worker_args,
        ):
            completed_batches += 1

            if ok and stage_tiled_table and stage_untiled_table:
                stage_tiled_tables.append(stage_tiled_table)
                stage_untiled_tables.append(stage_untiled_table)

            if not ok:
                errors.extend(batch_errors)

            log.info(
                "DGM1: %d/%d batches are completed. Finished batch %d/%d.",
                completed_batches,
                total,
                batch_idx,
                total,
            )

    if errors:
        raise RuntimeError(
            f"DGM1: {len(errors)} error(s) occurred during parallel batch import. First error: {errors[0]}"
        )

    return sorted(stage_tiled_tables), sorted(stage_untiled_tables)


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
    """Loads Bavaria DGM1 using batch imports.

    Workflow:
      * resolve required DGM1 tile URLs
      * resample selected tiles to target resolution
      * for every batch, import two stage tables:
          - tiled stage table
          - untiled stage table
      * merge tiled stages into final main table
      * merge untiled stages into temporary helper table
      * create raw overviews from helper table
      * retile raw overviews into regular 100x100 tiles
      * register retiled overviews to final main table
    """

    log = infdb.get_worker_logger()

    # ---------- 1. Read configuration ----------

    source_cfg = [infdb.get_toolname(), "sources", "opendata_bavaria"]
    dgm1_cfg = source_cfg + ["datasets", "gelaendemodell_1m"]

    schema = infdb.get_config_value(source_cfg + ["schema"])
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

    # utils.download_aria2c_many(infdb, urls, output_dir=str(dgm1_base_dir))

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

    # ---------- 6. Resample and import batches ----------

    target_table = f"{schema}.{table_base}"

    tmp_untiled_base = f"{table_base}_tmp_untiled_merged"
    tmp_untiled_table = f"{schema}.{tmp_untiled_base}"

    overview_factors = (4, 8, 16)
    overview_resampling = "NearestNeighbor"
    overview_tile_width = 100
    overview_tile_height = 100

    with infdb.connect() as db:
        db.execute_query(f"DROP TABLE IF EXISTS {target_table} CASCADE;")
        db.execute_query(f"DROP TABLE IF EXISTS {tmp_untiled_table} CASCADE;")

        for factor in overview_factors:
            db.execute_query(f"DROP TABLE IF EXISTS {schema}.o_{factor}_{table_base} CASCADE;")
            db.execute_query(f"DROP TABLE IF EXISTS {schema}.o_{factor}_{tmp_untiled_base} CASCADE;")

    stage_tiled_tables, stage_untiled_tables = _resample_and_import_dgm1_batches_in_parallel(
        infdb=infdb,
        tile_paths=tile_paths,
        resampled_dir=resampled_dir,
        dgm1_base_dir=dgm1_base_dir,
        source_srid=source_srid,
        target_res=target_res,
        schema=schema,
        table_base=table_base,
        batch_size=200,
        processes=10,
    )

    if not stage_tiled_tables or not stage_untiled_tables:
        log.warning("DGM1: no staging tables created; skipping final import.")
        return

    log.info(
        "DGM1: %d tiled staging tables and %d untiled staging tables created.",
        len(stage_tiled_tables),
        len(stage_untiled_tables),
    )

    # ---------- 7. Merge tiled stages into final main table ----------

    with infdb.connect() as db:
        db.execute_query(
            f"""
            CREATE TABLE {target_table} (
                rid SERIAL PRIMARY KEY,
                rast raster
            );
            """
        )

        for stage_table in stage_tiled_tables:
            db.execute_query(
                f"""
                INSERT INTO {target_table} (rast)
                SELECT rast FROM {stage_table};
                """
            )

        db.execute_query(
            f"""
            UPDATE {target_table}
            SET rast = ST_SetBandNoDataValue(
                ST_SetSRID(rast, {source_srid}),
                1,
                -9999
            );
            """
        )

        db.execute_query(
            f"""
            DELETE FROM {target_table}
            WHERE ST_Count(rast, 1, TRUE) = 0;
            """
        )

        db.execute_query(
            f"""
            SELECT AddRasterConstraints(
                '{schema}'::name,
                '{table_base}'::name,
                'rast'::name
            );
            """
        )

        db.execute_query(
            f"""
            CREATE INDEX IF NOT EXISTS {table_base}_rast_gix
            ON {target_table}
            USING GIST (ST_ConvexHull(rast));
            """
        )

        db.execute_query(f"ANALYZE {target_table};")

        log.info("DGM1: final tiled main table created: %s", target_table)

    # ---------- 8. Merge untiled stages into helper table ----------

    with infdb.connect() as db:
        db.execute_query(
            f"""
            CREATE TABLE {tmp_untiled_table} (
                rid SERIAL PRIMARY KEY,
                rast raster
            );
            """
        )

        for stage_table in stage_untiled_tables:
            db.execute_query(
                f"""
                INSERT INTO {tmp_untiled_table} (rast)
                SELECT rast FROM {stage_table};
                """
            )

        db.execute_query(
            f"""
            UPDATE {tmp_untiled_table}
            SET rast = ST_SetBandNoDataValue(
                ST_SetSRID(rast, {source_srid}),
                1,
                -9999
            );
            """
        )

        db.execute_query(
            f"""
            DELETE FROM {tmp_untiled_table}
            WHERE ST_Count(rast, 1, TRUE) = 0;
            """
        )

        db.execute_query(
            f"""
            SELECT AddRasterConstraints(
                '{schema}'::name,
                '{tmp_untiled_base}'::name,
                'rast'::name
            );
            """
        )

        db.execute_query(f"ANALYZE {tmp_untiled_table};")

        log.info("DGM1: merged untiled helper table created: %s", tmp_untiled_table)

    # ---------- 9. Create raw overviews, retile, and register ----------

    with infdb.connect() as db:
        for factor in overview_factors:
            raw_ov_name = f"o_{factor}_{tmp_untiled_base}"
            raw_ov_table = f"{schema}.{raw_ov_name}"

            final_ov_name = f"o_{factor}_{table_base}"
            final_ov_table = f"{schema}.{final_ov_name}"

            overview_scale_x = float(target_res) * factor
            overview_scale_y = -float(target_res) * factor

            log.info(
                "DGM1: creating raw overview %s from merged untiled table %s with factor %d.",
                raw_ov_table,
                tmp_untiled_table,
                factor,
            )

            db.execute_query(
                f"""
                SELECT ST_CreateOverview(
                    '{tmp_untiled_table}'::regclass,
                    'rast'::name,
                    {factor},
                    '{overview_resampling}'
                );
                """
            )

            db.execute_query(f"ANALYZE {raw_ov_table};")

            log.info(
                "DGM1: retiling raw overview %s into final overview %s.",
                raw_ov_table,
                final_ov_table,
            )

            db.execute_query(f"DROP TABLE IF EXISTS {final_ov_table} CASCADE;")

            db.execute_query(
                f"""
                CREATE TABLE {final_ov_table} AS
                WITH ext AS (
                    SELECT ST_Envelope(ST_Union(ST_ConvexHull(rast))) AS geom
                    FROM {raw_ov_table}
                )
                SELECT
                    row_number() OVER () AS rid,
                    r.rast
                FROM ext,
                LATERAL ST_Retile(
                    '{raw_ov_table}'::regclass,
                    'rast'::name,
                    ext.geom,
                    {overview_scale_x},
                    {overview_scale_y},
                    {overview_tile_width},
                    {overview_tile_height},
                    '{overview_resampling}'
                ) AS r(rast);
                """
            )

            stats = db.execute_query(
                f"""
                SELECT
                    COUNT(*) AS tiles,
                    COALESCE(SUM(ST_Count(rast, 1, TRUE)), 0) AS valid_pixels
                FROM {final_ov_table};
                """
            )

            log.info("DGM1: retiled overview stats for %s: %s", final_ov_table, stats)

            tiles = stats[0][0]
            valid_pixels = stats[0][1]

            if tiles == 0 or valid_pixels == 0:
                raise RuntimeError(
                    f"DGM1: retiled overview table {final_ov_table} is empty "
                    f"(tiles={tiles}, valid_pixels={valid_pixels})."
                )

            db.execute_query(
                f"""
                ALTER TABLE {final_ov_table}
                ADD PRIMARY KEY (rid);
                """
            )

            db.execute_query(
                f"""
                DROP INDEX IF EXISTS {schema}.{final_ov_name}_rast_gix;
                """
            )

            db.execute_query(
                f"""
                CREATE INDEX {final_ov_name}_rast_gix
                ON {final_ov_table}
                USING GIST (ST_ConvexHull(rast));
                """
            )

            db.execute_query(
                f"""
                SELECT AddRasterConstraints(
                    '{schema}'::name,
                    '{final_ov_name}'::name,
                    'rast'::name
                );
                """
            )

            meta = db.execute_query(
                f"""
                SELECT
                    srid,
                    scale_x,
                    scale_y,
                    blocksize_x,
                    blocksize_y,
                    nodata_values
                FROM raster_columns
                WHERE r_table_schema = '{schema}'
                  AND r_table_name = '{final_ov_name}';
                """
            )

            log.info("DGM1: retiled overview metadata for %s: %s", final_ov_table, meta)

            srid, scale_x, scale_y, blocksize_x, blocksize_y, nodata_values = meta[0]

            if srid != source_srid or scale_x is None or scale_y is None:
                raise RuntimeError(
                    f"DGM1: retiled overview table {final_ov_table} has invalid metadata: {meta}"
                )

            db.execute_query(
                f"""
                SELECT AddOverviewConstraints(
                    '{schema}'::name,
                    '{final_ov_name}'::name,
                    'rast'::name,
                    '{schema}'::name,
                    '{table_base}'::name,
                    'rast'::name,
                    {factor}
                );
                """
            )

            db.execute_query(f"ANALYZE {final_ov_table};")

            log.info(
                "DGM1: final overview %s registered as factor %d overview of %s.",
                final_ov_table,
                factor,
                target_table,
            )

    # ---------- 10. Cleanup temporary tables ----------

    with infdb.connect() as db:
        log.info("DGM1: cleaning up staging, helper, and raw overview tables.")

        for stage_table in stage_tiled_tables + stage_untiled_tables:
            db.execute_query(f"DROP TABLE IF EXISTS {stage_table} CASCADE;")

        for factor in overview_factors:
            raw_ov_table = f"{schema}.o_{factor}_{tmp_untiled_base}"
            db.execute_query(f"DROP TABLE IF EXISTS {raw_ov_table} CASCADE;")

        db.execute_query(f"DROP TABLE IF EXISTS {tmp_untiled_table} CASCADE;")

        rows = db.execute_query(
            f"""
            SELECT
                o_table_schema,
                o_table_name,
                r_table_schema,
                r_table_name,
                overview_factor
            FROM raster_overviews
            WHERE r_table_schema = '{schema}'
              AND r_table_name = '{table_base}'
            ORDER BY overview_factor;
            """
        )

        log.info("DGM1: registered raster overviews for %s: %s", target_table, rows)

        meta_rows = db.execute_query(
            f"""
            SELECT
                r_table_name,
                srid,
                scale_x,
                scale_y,
                blocksize_x,
                blocksize_y,
                same_alignment,
                regular_blocking,
                nodata_values
            FROM raster_columns
            WHERE r_table_schema = '{schema}'
              AND r_table_name IN (
                  '{table_base}',
                  'o_4_{table_base}',
                  'o_8_{table_base}',
                  'o_16_{table_base}'
              )
            ORDER BY scale_x;
            """
        )

        log.info("DGM1: raster metadata after overview registration: %s", meta_rows)

    log.info("DGM1: final tiled table + retiled overviews completed successfully.")


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

    # ==================== 7. FINALIZATION ====================
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