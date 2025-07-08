import os
import geopandas as gpd
import requests
from src.core import config

from src.services.loader import utils, logger


def load():
    logger.init_logger("infdb-loader", "infdb-loader.log")
    log = logger.get_logger("infdb-loader")

    if not utils.if_active("plz"):
        log.info("PLZ skips, status not active")
        return

    log.info("Loading PLZ data...")

    base_path = config.get_path(["loader", "sources", "plz", "path", "base"])
    os.makedirs(base_path, exist_ok=True)

    # processed_path = config.get_path(["loader", "sources", "plz", "path", "processed"])
    # os.makedirs(processed_path, exist_ok=True)

    filename = "plz-5stellig.geojson"
    path_file = os.path.join(base_path, filename)
    # print(path_file)

    if os.path.exists(path_file):
        log.info(f"File {filename} already exists.")
    else:
        # Datei herunterladen
        url = config.get_value(["loader", "sources", "plz", "url"])
        log.info(f"File {filename} will be downloaded from {url}")

        response = requests.get(url)
        with open(path_file, "wb") as file:
            file.write(response.content)
        log.info(f"{path_file} downloaded.")

    schema = config.get_value(["loader", "sources", "plz", "schema"])

    # Create schema if it doesn't exist
    sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"
    utils.sql_query(sql)

    prefix = config.get_value(["loader", "sources", "plz", "prefix"])
    layers = config.get_value(["loader", "sources", "plz", "layer"])

    print(gpd.list_layers(path_file)["name"])

    utils.import_layers(path_file, layers, schema, prefix=prefix)

    # for layer in gpd.list_layers(path_file)["name"]:
    #     print(f"Importing layer: {layer} into {schema}")
    #     gdf = gpd.read_file(path_file, layer=layer, bbox=gdf_envelope)
    #
    #     epsg = config.get_value(["services", "citydb", "epsg"])
    #     gdf.to_crs(epsg=epsg, inplace=True)
    #
    #     name = layer
    #     gdf.to_postgis(name, engine, if_exists='replace', schema=schema, index=False)
    #     gdf.to_file(os.path.join(processed_path, filename), layer=name, driver="GPKG")
