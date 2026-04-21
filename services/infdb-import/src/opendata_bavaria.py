import json
import logging
import multiprocessing as mp
import subprocess
from pathlib import Path

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


def _build_dgm1_single_ags_raster(
    ags_code: str,
    tool_name: str,
    config_path: str,
    dgm1_region_cfg: dict,
    dgm1_base_dir: str,
    source_srid: int,
    target_res: float,
) -> str | None:
    """Build one clipped raster for a single AGS from already-downloaded source tiles."""
    worker_log = log

    try:
        infdb = InfDB(tool_name=tool_name, config_path=config_path)
        worker_log = infdb.get_worker_logger()

        work_dir = Path(dgm1_base_dir)

        # Resolve AGS-specific URLs and corresponding local TIFFs
        urls = _build_urls_for_single_ags("DGM1 Bavaria", dgm1_region_cfg, ags_code, infdb, worker_log)
        if not urls:
            worker_log.info("DGM1 AGS %s: no URLs resolved, skipping.", ags_code)
            return None

        tile_paths = []
        for url in urls:
            tif_path = work_dir / Path(url).name
            if tif_path.exists() and tif_path.is_file():
                tile_paths.append(str(tif_path))

        tile_paths = sorted(set(tile_paths))

        if not tile_paths:
            worker_log.info("DGM1 AGS %s: no local TIFF files found, skipping.", ags_code)
            return None

        # Resolve AGS-specific exact clip geometry
        clip_wkt, _, _ = utils.get_clip_geometry(target_crs=source_srid, infdb=infdb, state_prefix=ags_code)
        if not clip_wkt:
            worker_log.info("DGM1 AGS %s: no clip geometry found, skipping.", ags_code)
            return None

        scope_geom = shapely_wkt.loads(clip_wkt)

        file_list_path = work_dir / f"dgm1_{ags_code}.txt"
        vrt_path = work_dir / f"dgm1_{ags_code}.vrt"
        mask_path = work_dir / f"mask_dgm1_{ags_code}.gpkg"
        clipped_tif = work_dir / f"dgm1_{ags_code}.tif"

        try:
            _write_file_list(tile_paths, file_list_path)

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
                worker_log.error("DGM1 AGS %s: gdalbuildvrt failed.", ags_code)
                return None

            gdf = gpd.GeoDataFrame(
                {"id": [1]},
                geometry=[scope_geom],
                crs=f"EPSG:{source_srid}",
            )
            gdf.to_file(mask_path, layer="mask", driver="GPKG")

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
                worker_log.error("DGM1 AGS %s: gdalwarp failed.", ags_code)
                return None

            if not clipped_tif.exists() or clipped_tif.stat().st_size == 0:
                worker_log.info("DGM1 AGS %s: clipped TIFF empty, skipping.", ags_code)
                return None

            worker_log.info("DGM1 AGS %s: raster prepared.", ags_code)
            return str(clipped_tif)

        finally:
            _cleanup_paths([file_list_path, vrt_path, mask_path], worker_log)

    except Exception:
        worker_log.exception("DGM1 AGS %s failed unexpectedly.", ags_code)
        return None


def _build_dgm1_ags_rasters_in_parallel(
    infdb: InfDB,
    ags_list: list[str],
    dgm1_region_cfg: dict,
    dgm1_base_dir: Path,
    source_srid: int,
    target_res: float,
    processes: int | None = None,
) -> list[str]:
    log = infdb.get_worker_logger()

    if not ags_list:
        log.warning("DGM1: no AGS values to process.")
        return []

    processes = max(1, min(processes, len(ags_list)))

    config_path = "../configs/config-infdb-import.yml"

    with mp.Pool(processes=processes) as pool:
        results = pool.starmap(
            _build_dgm1_single_ags_raster,
            [
                (
                    ags_code,
                    infdb.get_toolname(),
                    config_path,
                    dgm1_region_cfg,
                    str(dgm1_base_dir),
                    source_srid,
                    target_res,
                )
                for ags_code in ags_list
            ],
        )

    ags_rasters = [p for p in results if p]

    if len(ags_rasters) != len(ags_list):
        raise RuntimeError("DGM1: one or more AGS raster preparation jobs failed.")

    return ags_rasters


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
    raster_source_files = subprocess.check_output(
        [
            "find",
            str(dgm1_base_dir),
            "-maxdepth",
            "1",
            "-type",
            "f",
            "-iname",
            "*.tif",
            "-print",
        ],
        text=True,
    ).strip()

    if not raster_source_files:
        log.warning("DGM1: no .tif tiles found after download; skipping.")
        return

    tile_paths = raster_source_files.splitlines()
    log.info("DGM1: %d raster tiles available for clipping.", len(tile_paths))

    # ---------- 6. Resolve exact clip geometry ----------
    # We clip exactly to the real configured scope, but the tile
    # download step is done once on the statewide grid.
    ags_list = utils.fetch_scope_ags_from_db(infdb)
    if not ags_list:
        log.warning("DGM1: no AGS resolved from scope; skipping.")
        return

    # ---------- 8. Clip / merge all tiles into one raster ----------
    ags_rasters = _build_dgm1_ags_rasters_in_parallel(
        infdb=infdb,
        ags_list=ags_list,
        dgm1_region_cfg=dgm1_region_cfg,
        dgm1_base_dir=dgm1_base_dir,
        source_srid=source_srid,
        target_res=target_res,
        processes=utils.get_number_processes(infdb),
    )

    final_file_list_path = dgm1_base_dir / "dgm1_scope.txt"
    final_vrt_path = dgm1_base_dir / "dgm1_scope.vrt"
    output_tif = dgm1_base_dir / f"dgm1_{target_res}m_clipped.tif"

    try:
        _write_file_list(ags_rasters, final_file_list_path)

        rc = utils.do_cmd(
            infdb,
            [
                "gdalbuildvrt",
                "-input_file_list",
                str(final_file_list_path),
                str(final_vrt_path),
            ],
        )
        if rc != 0:
            raise RuntimeError("DGM1: failed to build final scope VRT.")

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
                str(final_vrt_path),
                str(output_tif),
            ],
        )
        if rc != 0:
            raise RuntimeError("DGM1: failed to create final merged raster.")

        # ---------- 9. Validate output ----------
        try:
            size_mb = output_tif.stat().st_size / 1_000_000
        except FileNotFoundError:
            log.error("DGM1: clipped raster not found at %s", output_tif)
            return

        if size_mb <= 0:
            log.warning("DGM1: clipped raster is empty; skipping import.")
            output_tif.unlink(missing_ok=True)
            return

        log.info("DGM1: created clipped raster (%.1f MB)", size_mb)

        # ---------- 10. Import into PostGIS ----------
        target_table = f"{schema}.{table_base}"

        with infdb.connect() as db:
            db.execute_query(f"DROP TABLE IF EXISTS {target_table};")

        pgurl = utils._pg_connstring_for_psql(infdb)
        psql_cmd = f'psql --no-psqlrc -q -v ON_ERROR_STOP=1 -X "{pgurl}"'

        import_pipeline = (
            f'raster2pgsql -q -s {source_srid} -I -C -M -N -9999 -t 100x100 -l 4,8,16 "{output_tif}" {target_table} | {psql_cmd}'
        )

        log.info("DGM1: importing into %s", target_table)
        utils.do_cmd(infdb, import_pipeline, shell=True)
        log.info("DGM1: import finished.")

    finally:
        _cleanup_paths(
            [final_file_list_path, final_vrt_path, output_tif] + [Path(p) for p in ags_rasters],
            log,
        )


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
