"""Imports the Solarkataster NRW (rooftop PV potential) for the NRW municipalities in scope.

The Solarkataster NRW of the state agency LANUK provides one record per roof surface with the
installable PV capacity, module count, orientation, tilt and annual yield. It is derived from an
airborne laser scan surface model (0.5 m) and accounts for shading and roof structures. The data
is published per municipality as Shape file under the licence dl-de/zero-2.0:
https://www.opengeodata.nrw.de/produkte/umwelt_klima/energie/solarkataster/photovoltaik/

The field ``name`` holds the ALKIS building ID, which equals ``objectid`` of the LoD2 buildings
(e.g. ``basedata.buildings.objectid``), so the potential can be joined to buildings directly.

Tables (``<schema>.<prefix>_...``):
    ``<prefix>_pv_dach``: one row per roof surface.
    ``<prefix>_import``: one row per imported municipality (source file, version, totals). A
        building of an imported municipality without a roof surface has no roof suited for PV.
"""

import datetime as dt
import multiprocessing as mp
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import geopandas as gpd
import pandas as pd
import requests
import shapely
from pyinfdb import InfDB
from sqlalchemy import text

from . import utils

SOURCE: str = "solarkataster-nrw"
NRW_STATE_PREFIX: str = "05"
SOURCE_EPSG: int = 25832
AGS_IN_FILE_NAME = re.compile(r"_(05\d{6})_")

# Target column -> (Shape field, SQL type, comment). Shape field names are cut to 10 characters.
COLUMNS: Dict[str, tuple[str, str, str]] = {
    "objectid": ("name", "text", "ALKIS building ID (= objectid of the LoD2 building)"),
    "gemeindeschluessel": ("gem_kn", "text", "Municipality key (AGS)"),
    "lanuk_id": ("LANUK_ID", "text", "ID of the roof surface in the Solarkataster NRW"),
    "geb_id": ("geb_id", "text", "Building ID in the Solarkataster NRW"),
    "mod_id": ("mod_id", "text", "Module layout ID in the Solarkataster NRW"),
    "dachtyp": ("dachtyp", "text", "Roof type (flach = flat, geneigt = pitched)"),
    "richtung": ("richtung", "integer", "Azimuth in degree (180 = south, -1 = flat roof)"),
    "neigung": ("neigung", "integer", "Tilt in degree"),
    "himmel_kat": ("himmel_kat", "text", "Orientation category"),
    "modarea": ("modarea", "double precision", "Roof area suited for modules in m2"),
    "anzahl": ("anzahl", "integer", "Number of modules"),
    "modanetto": ("modanetto", "double precision", "Net module area in m2"),
    "kw": ("kw", "double precision", "Installable PV capacity in kWp"),
    "kwh_kwp": ("kwh_kwp", "double precision", "Specific annual yield in kWh/kWp"),
    "str": ("str", "double precision", "Annual electricity yield in kWh"),
    "yr_median": ("yr_median", "double precision", "Median annual irradiation in kWh/m2"),
    "jahr": ("jahr", "integer", "Year of the laser scan flight"),
}
INTEGER_COLUMNS: List[str] = [column for column, (_, sql_type, _) in COLUMNS.items() if sql_type == "integer"]


def load(infdb: InfDB) -> None:
    """Imports the Solarkataster NRW for every NRW municipality (AGS 05...) in scope.

    Each municipality is replaced in one transaction, so a rerun does not duplicate rows.

    Args:
        infdb: InfDB facade with the infdb-import configuration.
    """
    log = infdb.get_worker_logger()
    try:
        if not utils.if_active(SOURCE, infdb):
            return

        schema = _source_config(infdb, "schema")
        prefix = _source_config(infdb, "prefix")
        ags_list = [ags for ags in utils.fetch_scope_ags_from_db(infdb) if ags.startswith(NRW_STATE_PREFIX)]
        if not ags_list:
            log.info("%s: no NRW municipality in scope, nothing to import.", SOURCE)
            sys.exit(0)

        files = find_shape_files(_source_config(infdb, "url"), _source_config(infdb, "dataset"))
        missing = sorted(set(ags_list) - set(files))
        if missing:
            log.error("%s: no Shape file for AGS %s", SOURCE, missing)

        _create_tables(infdb, schema, prefix)

        tasks = [
            (ags, files[ags], infdb.get_toolname(), infdb.config_path, schema, prefix)
            for ags in ags_list
            if ags in files
        ]
        with mp.Pool(processes=utils.get_number_processes(infdb)) as pool:
            results = pool.starmap(process_municipality, tasks)

        if missing or not all(results):
            raise RuntimeError("Some municipalities failed to import")
        sys.exit(0)
    except Exception as err:
        log.exception("An error occurred while processing %s: %s", SOURCE, str(err))
        sys.exit(1)


def find_shape_files(url: str, dataset: str) -> Dict[str, Dict[str, Any]]:
    """Lists the Shape file of each municipality from the ``index.json`` of the download page.

    Args:
        url: Download page that holds ``index.json``.
        dataset: Name of the dataset in ``index.json`` that holds the per-municipality files.

    Returns:
        Mapping AGS -> file entry (``name``, ``size``, ``timestamp``) with ``url`` added.

    Raises:
        ValueError: If the dataset is not listed in ``index.json``.
    """
    base_url = url.rstrip("/") + "/"
    response = requests.get(base_url + "index.json", timeout=utils.HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    datasets = {entry["name"]: entry["files"] for entry in response.json()["datasets"]}
    if dataset not in datasets:
        raise ValueError(f"Dataset {dataset!r} not in {base_url}index.json (found: {sorted(datasets)})")

    files: Dict[str, Dict[str, Any]] = {}
    for entry in datasets[dataset]:
        match = AGS_IN_FILE_NAME.search(entry["name"])
        if match:
            files[match.group(1)] = {**entry, "url": base_url + entry["name"]}
    return files


def process_municipality(
    ags: str, entry: Dict[str, Any], tool_name: str, config_path: Optional[str], schema: str, prefix: str
) -> bool:
    """Downloads, reads and writes the roof surfaces of one municipality.

    Args:
        ags: Municipality key.
        entry: File entry from ``find_shape_files``.
        tool_name: Tool name of the InfDB configuration.
        config_path: Path of the configuration file, to set up InfDB in the worker process.
        schema: Target schema.
        prefix: Table name prefix.

    Returns:
        True on success, False if an error was logged.
    """
    infdb = InfDB(tool_name=tool_name, config_path=config_path)
    log = infdb.get_worker_logger()
    try:
        log.info("%s: importing %s (%.0f MB)", SOURCE, entry["name"], int(entry["size"]) / 1e6)
        zip_dir = _source_path(infdb, "zip")
        zip_file = utils.download_files(entry["url"], zip_dir, infdb)[0]
        unzip_dir = os.path.join(_source_path(infdb, "unzip"), ags)
        utils.unzip(zip_file, unzip_dir, infdb)

        shape_files = utils.get_all_files(unzip_dir, ".shp")
        if len(shape_files) != 1:
            raise ValueError(f"Expected one Shape file in {unzip_dir}, found {len(shape_files)}")
        epsg = int(infdb.get_db_parameters_dict()["epsg"])
        surfaces = read_roof_surfaces(shape_files[0], epsg)

        other = sorted(set(surfaces["gemeindeschluessel"]) - {ags})
        if other:
            log.warning("%s: %s contains roof surfaces of other municipalities %s", SOURCE, entry["name"], other)

        _write_municipality(infdb, surfaces, ags, entry, schema, prefix)
        log.info("%s: %s done, %d roof surfaces, %.1f MWp", SOURCE, ags, len(surfaces), surfaces["kw"].sum() / 1e3)
        return True
    except Exception as err:
        log.exception("%s: import of %s failed: %s", SOURCE, ags, str(err))
        return False


def read_roof_surfaces(shape_file: str, epsg: int) -> gpd.GeoDataFrame:
    """Reads the roof surfaces of one Shape file into the target columns.

    Args:
        shape_file: Path of the Shape file.
        epsg: EPSG code of the database.

    Returns:
        GeoDataFrame with the columns of ``COLUMNS`` and MultiPolygon geometries in ``geom``.

    Raises:
        ValueError: If the CRS or a field differs from the expected source format.
    """
    fields = [field for field, _, _ in COLUMNS.values()]
    surfaces = gpd.read_file(shape_file, columns=fields, engine="pyogrio")
    if surfaces.crs is None or surfaces.crs.to_epsg() != SOURCE_EPSG:
        raise ValueError(f"Unexpected CRS {surfaces.crs} in {shape_file}, expected EPSG:{SOURCE_EPSG}")
    missing = sorted(set(fields) - set(surfaces.columns))
    if missing:
        raise ValueError(f"Fields {missing} missing in {shape_file}")

    surfaces = surfaces.rename(columns={field: column for column, (field, _, _) in COLUMNS.items()})
    for column in INTEGER_COLUMNS:
        surfaces[column] = pd.to_numeric(surfaces[column]).round().astype("Int64")
    surfaces = surfaces.rename_geometry("geom").to_crs(epsg=epsg)
    # Shape files mix Polygon and MultiPolygon; the table holds MultiPolygon only.
    is_polygon = surfaces.geom_type == "Polygon"
    polygons = surfaces.geometry[is_polygon].to_numpy().reshape(-1, 1)  # one part per MultiPolygon
    surfaces.loc[is_polygon, "geom"] = shapely.multipolygons(polygons)
    return surfaces[[*COLUMNS, "geom"]]


def _write_municipality(
    infdb: InfDB, surfaces: gpd.GeoDataFrame, ags: str, entry: Dict[str, Any], schema: str, prefix: str
) -> None:
    """Replaces the roof surfaces of one municipality and records the import in one transaction."""
    keys = sorted(set(surfaces["gemeindeschluessel"]) | {ags})
    with infdb.get_db_engine().begin() as connection:
        connection.execute(
            text(f"DELETE FROM {schema}.{prefix}_pv_dach WHERE gemeindeschluessel = ANY(:keys)"), {"keys": keys}
        )
        surfaces.to_postgis(f"{prefix}_pv_dach", connection, schema=schema, if_exists="append", index=False)
        connection.execute(
            text(f"""
                INSERT INTO {schema}.{prefix}_import
                    (ags, file_name, file_timestamp, imported_at, roof_surfaces, kw_total)
                VALUES (:ags, :file_name, :file_timestamp, :imported_at, :roof_surfaces, :kw_total)
                ON CONFLICT (ags) DO UPDATE SET
                    file_name = EXCLUDED.file_name,
                    file_timestamp = EXCLUDED.file_timestamp,
                    imported_at = EXCLUDED.imported_at,
                    roof_surfaces = EXCLUDED.roof_surfaces,
                    kw_total = EXCLUDED.kw_total
            """),
            {
                "ags": ags,
                "file_name": entry["name"],
                "file_timestamp": entry.get("timestamp"),
                "imported_at": dt.datetime.now(dt.timezone.utc),
                "roof_surfaces": len(surfaces),
                "kw_total": float(surfaces["kw"].sum()),
            },
        )


def _create_tables(infdb: InfDB, schema: str, prefix: str) -> None:
    """Creates schema, tables, indexes and comments if missing (before the worker processes start)."""
    epsg = int(infdb.get_db_parameters_dict()["epsg"])
    surfaces = f"{schema}.{prefix}_pv_dach"
    imports = f"{schema}.{prefix}_import"
    columns = ",\n".join(f"{column} {sql_type}" for column, (_, sql_type, _) in COLUMNS.items())
    column_comments = "\n".join(
        f"COMMENT ON COLUMN {surfaces}.{column} IS '{comment}';" for column, (_, _, comment) in COLUMNS.items()
    )
    with infdb.connect() as db:
        db.execute_query(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        db.execute_query(f"""
            CREATE TABLE IF NOT EXISTS {surfaces} (
                {columns},
                geom geometry(MultiPolygon, {epsg})
            );
            CREATE INDEX IF NOT EXISTS {prefix}_pv_dach_objectid_idx ON {surfaces} (objectid);
            CREATE INDEX IF NOT EXISTS {prefix}_pv_dach_gemeindeschluessel_idx ON {surfaces} (gemeindeschluessel);
            CREATE INDEX IF NOT EXISTS {prefix}_pv_dach_geom_idx ON {surfaces} USING GIST (geom);
            CREATE TABLE IF NOT EXISTS {imports} (
                ags text PRIMARY KEY,
                file_name text NOT NULL,
                file_timestamp timestamp,
                imported_at timestamptz NOT NULL,
                roof_surfaces integer NOT NULL,
                kw_total double precision NOT NULL
            );
            COMMENT ON TABLE {surfaces} IS
                'Solarkataster NRW (LANUK): roof surfaces suited for PV, dl-de/zero-2.0';
            COMMENT ON TABLE {imports} IS
                'Imported municipalities; a building there without roof surface has no roof suited for PV';
            {column_comments}
        """)


def _source_config(infdb: InfDB, key: str) -> Any:
    """Returns a value of the source configuration."""
    return infdb.get_config_value([infdb.get_toolname(), "sources", SOURCE, key])


def _source_path(infdb: InfDB, key: str) -> str:
    """Returns a directory of the source configuration and creates it if missing."""
    path = infdb.get_config_path([infdb.get_toolname(), "sources", SOURCE, "path", key], type="loader")
    Path(path).mkdir(parents=True, exist_ok=True)
    return path
