import os
import sys
from zipfile import ZipFile, BadZipFile

from pyinfdb import InfDB
from shapely import wkt as shapely_wkt
from shapely.geometry import box
import multiprocessing as mp

from . import utils


def _urls_to_local_citygml_paths(urls: list[str], gml_path: str, log) -> list[str]:
    """Resolve current-run URLs to existing local CityGML file paths.

    Supports:
    - direct .gml files
    - .zip files containing .gml files

    Important:
    This function only resolves files belonging to the current URL list.
    It does not import every file in the shared CityGML folder.
    """
    local_files = []
    missing_files = []

    for url in urls:
        filename = os.path.basename(url)
        local_path = os.path.join(gml_path, filename)

        if not os.path.isfile(local_path):
            missing_files.append(local_path)
            continue

        if filename.lower().endswith(".gml"):
            local_files.append(local_path)
            continue

        if filename.lower().endswith(".zip"):
            try:
                with ZipFile(local_path, "r") as zf:
                    gml_members = [
                        member
                        for member in zf.namelist()
                        if member.lower().endswith(".gml")
                    ]

                    if not gml_members:
                        log.warning("LoD2 ZIP contains no GML files: %s", local_path)
                        continue

                    for member in gml_members:
                        extracted_filename = os.path.basename(member)

                        if not extracted_filename:
                            continue

                        extracted_path = os.path.join(gml_path, extracted_filename)

                        if not os.path.isfile(extracted_path):
                            with zf.open(member) as src, open(extracted_path, "wb") as dst:
                                dst.write(src.read())

                        local_files.append(extracted_path)

            except BadZipFile:
                log.warning("LoD2 invalid ZIP file: %s", local_path)

            continue

        log.warning("LoD2 unsupported file type: %s", local_path)

    if missing_files:
        log.warning("LoD2: %d expected files are missing after download.", len(missing_files))
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


def _import_lod2_batch(
    batch_files: list[str],
    tool_name: str,
    batch_index: int,
    total_batches: int,
) -> bool:
    """Import one batch of GML files directly with citydb."""
    try:
        infdb = InfDB(tool_name=tool_name, config_path="../configs/config-infdb-import.yml")
        log = infdb.get_worker_logger()

        if not batch_files:
            log.info("LoD2 batch %d/%d: empty batch, skipping.", batch_index, total_batches)
            return True

        source_cfg = [infdb.get_toolname(), "sources", "lod2"]
        params = infdb.get_db_parameters_dict()
        import_mode = infdb.get_config_value(source_cfg + ["import-mode"]) or "skip"

        log.info(
            "LoD2 batch %d/%d: importing %d files.",
            batch_index,
            total_batches,
            len(batch_files),
        )

        cmd_parts = [
            "citydb",
            "import",
            "citygml",
            "-H",
            params["host"],
            "-d",
            params["db"],
            "-u",
            params["user"],
            "-p",
            params["password"],
            "-P",
            str(params["exposed_port"]),
            f"--import-mode={import_mode}",
            *batch_files,
        ]

        return_code = utils.do_cmd(infdb, cmd_parts)

        if return_code != 0:
            log.error(
                "LoD2 batch %d/%d failed with return code %d.",
                batch_index,
                total_batches,
                return_code,
            )
            return False

        log.info("LoD2 batch %d/%d imported successfully.", batch_index, total_batches)
        return True

    except Exception:
        if "log" in locals():
            log.exception("LoD2 batch %d/%d failed unexpectedly.", batch_index, total_batches)
        return False


def _import_lod2_files_in_parallel(
    infdb: InfDB,
    gml_files: list[str],
    batch_size: int = 200,
    processes: int | None = None,
) -> bool:
    """Import current-run GML files in parallel batches."""
    log = infdb.get_worker_logger()

    if not gml_files:
        log.warning("LoD2: no GML files to import.")
        return True

    batches = _chunk_list(gml_files, batch_size)
    total_batches = len(batches)

    if processes is None:
        processes = utils.get_number_processes(infdb)

    processes = max(1, min(processes, total_batches))

    log.info(
        "LoD2: importing %d files in %d batches with %d worker(s).",
        len(gml_files),
        total_batches,
        processes,
    )

    with mp.Pool(processes=processes) as pool:
        results = pool.starmap(
            _import_lod2_batch,
            [
                (batch, infdb.get_toolname(), i + 1, total_batches)
                for i, batch in enumerate(batches)
            ],
        )

    return all(results)


def _iter_tile_origins_for_geom(
    geom,
    tile_size_m: int,
    offset_x_m: int = 0,
    offset_y_m: int = 0,
):
    """Yield lower-left tile origin coordinates in meters for all tiles
    intersecting the given geometry.
    """
    minx, miny, maxx, maxy = geom.bounds

    start_x = int((minx - offset_x_m) // tile_size_m) * tile_size_m + offset_x_m
    start_y = int((miny - offset_y_m) // tile_size_m) * tile_size_m + offset_y_m
    end_x = int((maxx - offset_x_m) // tile_size_m) * tile_size_m + offset_x_m
    end_y = int((maxy - offset_y_m) // tile_size_m) * tile_size_m + offset_y_m

    for x in range(start_x, end_x + tile_size_m, tile_size_m):
        for y in range(start_y, end_y + tile_size_m, tile_size_m):
            cell = box(x, y, x + tile_size_m, y + tile_size_m)
            if geom.intersects(cell):
                yield (x, y)


def _build_urls_for_region(region_name: str, region_cfg: dict, infdb: InfDB, log) -> list[str]:
    """Build all tiled dataset URLs for one region based on the scoped geometry.

    This helper is intentionally generic so it can be reused for multiple
    tiled OpenData sources, for example:
      - LoD2 NRW
      - LoD2 Bavaria
      - LoD2 Baden-Württemberg

    Expected config keys in region_cfg:
      - status: "active" / "not-active"
      - state_prefix: AGS prefix used to resolve the clip geometry
      - base_url: URL prefix of the tiled dataset
      - tile_size_m: tile size in meters
      - filename_template: filename pattern using:
            {e_km} = easting in km
            {n_km} = northing in km

    Optional config keys:
      - tile_origin_offset_x_m
      - tile_origin_offset_y_m
    """
    if region_cfg.get("status") != "active":
        log.info("%s: inactive, skipping.", region_name)
        return []

    state_prefix = region_cfg.get("state_prefix")
    base_url = str(region_cfg.get("base_url", "")).rstrip("/") + "/"
    tile_size_m = int(region_cfg.get("tile_size_m") or 0)
    offset_x_m = int(region_cfg.get("tile_origin_offset_x_m") or 0)
    offset_y_m = int(region_cfg.get("tile_origin_offset_y_m") or 0)
    template = region_cfg.get("filename_template")

    if not state_prefix or not base_url or not tile_size_m or not template:
        log.warning("%s: incomplete tiled dataset configuration, skipping.", region_name)
        return []

    # Resolve the scoped geometry once for the configured state/region.
    # We use EPSG:25832 because these datasets use meter-based projected tiles.
    clip_wkt, _, _ = utils.get_clip_geometry(
        target_crs=25832,
        infdb=infdb,
        state_prefix=state_prefix,
    )

    if not clip_wkt:
        log.info("%s: no scope geometry resolved for state prefix %s, skipping.", region_name, state_prefix)
        return []

    scope_geom = shapely_wkt.loads(clip_wkt)

    urls = []
    for x, y in _iter_tile_origins_for_geom(
        scope_geom,
        tile_size_m=tile_size_m,
        offset_x_m=offset_x_m,
        offset_y_m=offset_y_m,
    ):
        # Convert tile origin coordinates from meters to kilometer indices,
        # because Bavaria/NRW/BW filenames are based on km grid references.
        fname = template.format(
            e_km=x // 1000,
            n_km=y // 1000,
        )
        urls.append(base_url + fname)

    urls = sorted(set(urls))
    log.info("%s: %d intersecting tiles resolved.", region_name, len(urls))
    return urls



def load(infdb: InfDB) -> bool:
    """Download LoD2 CityGML tiles for all active configured regions, import them via citydb,
    then create the flat LoD2 building table.

    Behavior:
    - Uses one shared CityGML folder for all configured regions.
    - Resolves scope geometry per region/state in EPSG:25832.
    - Computes intersecting tiles using regular grid logic.
    - Deduplicates URLs globally, so the same file is not downloaded twice.
    - Supports direct .gml files and .zip files containing .gml files.
    - Imports only the current-run files, not the whole folder.
    """
    log = infdb.get_worker_logger()

    try:
        if not utils.if_active("lod2", infdb):
            return True

        source_cfg = [infdb.get_toolname(), "sources", "lod2"]

        gml_path = infdb.get_config_path(source_cfg + ["path", "gml"], type="loader")
        os.makedirs(gml_path, exist_ok=True)

        nrw_cfg = infdb.get_config_value(source_cfg + ["nrw"]) or {}
        bavaria_cfg = infdb.get_config_value(source_cfg + ["bavaria"]) or {}
        bw_cfg = infdb.get_config_value(source_cfg + ["baden_wuerttemberg"]) or {}

        urls = []
        urls.extend(_build_urls_for_region("NRW", nrw_cfg, infdb, log))
        urls.extend(_build_urls_for_region("Bavaria", bavaria_cfg, infdb, log))
        urls.extend(_build_urls_for_region("Baden-Württemberg", bw_cfg, infdb, log))

        urls = sorted(set(urls))
        log.info("LoD2: %d unique tiles to download across all active regions.", len(urls))

        if not urls:
            log.warning("LoD2: no tiles resolved for any active region; skipping import.")
            return True

        # Download all unique tiles into one shared folder.
        # NRW / Bavaria download .gml files.
        # Baden-Württemberg downloads .zip files.
        utils.download_aria2c_many(infdb, urls, output_dir=gml_path)

        # Resolve only the files for the current run / current scope.
        # ZIP files are extracted into the same CityGML folder and their
        # extracted .gml files are returned.
        gml_files = _urls_to_local_citygml_paths(urls, gml_path, log)

        if not gml_files:
            log.warning("LoD2: no downloaded/extracted GML files found for current scope; skipping import.")
            return True

        success = _import_lod2_files_in_parallel(
            infdb=infdb,
            gml_files=gml_files,
            batch_size=200,
            processes=utils.get_number_processes(infdb),
        )

        if not success:
            raise RuntimeError("LoD2: one or more import batches failed")

        # Create flat building table
        object_id_prefix = infdb.get_config_value(source_cfg + ["object_id_prefix"]) or "DE"
        utils.create_building_lod2_table(object_id_prefix=object_id_prefix, infdb=infdb)

        log.info("LoD2 data loaded successfully")
        sys.exit(0)

    except Exception:
        log.exception("An error occurred while processing LoD2 data")
        sys.exit(1)