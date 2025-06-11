import os
import geopandas as gpd
import requests
from data_import.imp import config, utils


def import_plz():

    # Create a database-data-import-container connection
    engine = utils.get_engine()

    # Get envelope
    sql = "SELECT geometry as geom FROM general.envelope"
    gdf_envelope = gpd.read_postgis(sql, engine, geom_col="geom")

    base_path = config.get_path(["opendata", "plz", "plz_dir"])
    processed_path = config.get_path(["opendata", "plz", "plz_processed_dir"])
    os.makedirs(base_path, exist_ok=True)
    os.makedirs(processed_path, exist_ok=True)

    filename = "plz-5stellig.geojson"
    path_file = os.path.join(base_path, filename)
    print(path_file)

    if os.path.exists(path_file):
        print(f"File {filename} already exists.")
    else:
        # Datei herunterladen
        url = config.get_value(["opendata", "plz", "url"])
        print(f"File {filename} will be downloaded from {url}")

        response = requests.get(url)
        with open(path_file, "wb") as file:
            file.write(response.content)
        print(f"{path_file} downloaded.")

    schema = config.get_value(["opendata", "plz", "schema"])

    # Create schema if it doesn't exist
    sql=f"CREATE SCHEMA IF NOT EXISTS {schema};"
    utils.sql_query(sql)

    for layer in gpd.list_layers(path_file)["name"]:
        print(f"Importing layer: {layer} into {schema}")
        gdf = gpd.read_file(path_file, layer=layer, bbox=gdf_envelope)

        epsg = config.epsg
        gdf.to_crs(epsg=epsg, inplace=True)

        name = layer
        gdf.to_postgis(name, engine, if_exists='replace', schema=schema, index=False)
        gdf.to_file(os.path.join(processed_path, filename), layer=name, driver="GPKG")


import_plz()