import os
import logging
import multiprocessing
import chardet
import pandas as pd
import geopandas as gpd
from . import utils, config, logger

log = logging.getLogger(__name__)


def load(log_queue):
    logger.setup_worker_logger(log_queue)

    if not utils.if_active("zensus_2022"):
        return
    
    datasets = config.get_value(["loader", "sources", "zensus_2022", "datasets"])

    url = config.get_value(["loader", "sources", "zensus_2022", "url"])
    zip_links = utils.get_website_links(url)

    # Validate links
    yaml_links = {entry["url"] for entry in datasets}
    original_set = set(zip_links)

    missing_in_yaml = original_set - yaml_links
    extra_in_yaml = yaml_links - original_set
    if missing_in_yaml:
        log.warning("Links in original list but NOT in YAML:")
        for l in sorted(missing_in_yaml):
            log.warning(f" - {l}")

    if extra_in_yaml:
        log.warning("Links in YAML but NOT in original list:")
        for l in sorted(extra_in_yaml):
            log.warning(f" - {l}")

    # Create schema if it doesn't exist
    schema = config.get_value(["loader", "sources", "zensus_2022", "schema"])
    sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"
    utils.sql_query(sql)
    
    # Create folders
    zip_path = config.get_path(["loader", "sources", "zensus_2022", "path", "zip"])
    os.makedirs(zip_path, exist_ok=True)
    unzip_path = config.get_path(["loader", "sources", "zensus_2022", "path", "unzip"])
    os.makedirs(unzip_path, exist_ok=True)

    number_processes = utils.get_number_processes()
    with multiprocessing.Pool(
        processes=number_processes,
        initializer=logger.setup_worker_logger,
        initargs=(log_queue,),
    ) as pool:
        results = pool.map(process_dataset, datasets)


def process_dataset(dataset):
    log.info(f"Working on {dataset["name"]}")

    # Check for status
    status = dataset["status"]
    if status == "active":
        log.info(f"Loading {dataset["name"]} ...")
    else:
        log.info(f"{dataset["name"]} skips, status not active")
        return True
    
    # Check for year 
    years = config.get_value(["loader", "sources", "zensus_2022", "years"])
    if dataset["year"] not in years:
        log.info(f"{dataset["name"]} skips, not in years list")
        return True
        
    # Download
    zip_path = config.get_path(["loader", "sources", "zensus_2022", "path", "zip"])
    download_path = os.path.join(zip_path, dataset["table_name"] + ".zip")
    link = dataset["url"]
    utils.download_files(link, download_path)

    # Unzip
    unzip_path = config.get_path(["loader", "sources", "zensus_2022", "path", "unzip"])
    folder_path = os.path.join(unzip_path, dataset["table_name"])
    utils.unzip(download_path, folder_path)

    # Export to postgis
    resolutions = config.get_value(["loader", "sources", "zensus_2022", "resolutions"])
    for resolution in resolutions:
        log.info(f"Processing {dataset["name"]} with {resolution} ...")

        # Search for corresponding file within source folder
        file = utils.get_file(folder_path, resolution, ".csv")
        if not file:
            log.warning(f"No file for {dataset["name"]} with resolution {resolution} found")
            continue

        try:
            csv_path = file

            with open(csv_path, "rb") as f:
                raw_bytes = f.read(1000)
                detected_encoding = chardet.detect(raw_bytes)["encoding"]
                log.debug(f"Detected encoding for {csv_path}: {detected_encoding}")

            # csv_path = utils.ensure_utf8_encoding(csv_path)  # <-- check and fix encoding
            df = pd.read_csv(
                csv_path,
                sep=";",
                decimal=",",
                na_values="–",
                low_memory=False,
                encoding=detected_encoding,
            )  # , encoding="latin_1"   # GeoDataFrame laden (Beispiel) nrows=10,

            df.fillna(0, inplace=True)
            df.columns = df.columns.str.lower()

            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(
                    df.loc[:, "x_mp_" + resolution], df.loc[:, "y_mp_" + resolution]
                ),
                crs="EPSG:3035",
            )  # ETRS89 / UTM zone 32N
            epsg = utils.get_db_parameters("citydb")["epsg"]
            gdf = gdf.to_crs(epsg=epsg)

            # Create a database-data-import-container connection
            engine = utils.get_db_engine("citydb")

            # Get user configurations
            prefix = config.get_value(["loader", "sources", "zensus_2022", "prefix"])
            schema = config.get_value(["loader", "sources", "zensus_2022", "schema"])

            # Get envelope
            gdf_envelope = utils.get_envelop()
            if not gdf_envelope.empty:
                gdf_clipped = gpd.clip(gdf, gdf_envelope)
            else:
                gdf_clipped = gdf

            table_name = dataset["table_name"]
            table_name = prefix + "_" + str(dataset["year"])[-2:] + "_" + resolution + "_" + dataset["table_name"]

            gdf_clipped.to_postgis(table_name, engine, if_exists='replace', schema=schema, index=False)

            # Save clipped data locally
            save_local = config.get_value(["loader", "sources", "zensus_2022", "save_local"])
            if save_local == "active":
                output_path = config.get_path(
                    ["loader", "sources", "zensus_2022", "path", "processed"]
                )
                log.debug(f"Output path: {output_path}")
                os.makedirs(output_path, exist_ok=True)

                gdf_clipped.to_file(
                    os.path.join(output_path, f"zenus-2022_{resolution}.gpkg"),
                    layer=table_name,
                    driver="GPKG",
                )
                gdf_clipped.to_csv(
                    os.path.join(output_path, f"zenus-2022_{resolution}_{table_name}.csv"),
                    index=False,
                )

            log.info(f"Processed sucessfully {file}")

        except Exception as err:
            log.exception("An error occurred while processing file: %s", file)
            return False
    
    return True