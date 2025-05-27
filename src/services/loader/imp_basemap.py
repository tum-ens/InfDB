import os
import geopandas as gpd
from src.services.loader import utils
from src.core.config import config


def import_basemap():
    status = config["opendata"]["basemap"]["status"]
    if status != "active":
        print("basemap skips, status not active")
        return

    engine = utils.get_engine()

    # Get envelope
    sql = "SELECT geometry as geom FROM general.envelope"
    gdf_envelope = gpd.read_postgis(sql, engine)

    base_path = config["opendata"]["basemap"]["basemap_dir"]
    processed_path = config["opendata"]["basemap"]["basemap_processed_dir"]
    os.makedirs(base_path, exist_ok=True)
    os.makedirs(processed_path, exist_ok=True)

    site_url = config["opendata"]["basemap"]["url"]
    ending = config["opendata"]["basemap"]["ending"]
    filter = config["opendata"]["basemap"]["filter"]
    urls = utils.get_links(site_url, ending, filter)

    download_files = utils.download_files(urls, base_path)

    schema = config["opendata"]["basemap"]["schema"]
    # Create schema if it doesn't exist
    sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"
    utils.sql_query(sql)

    for file in download_files:

        for layer in gpd.list_layers(file)["name"]:
            print(f"Importing layer: {layer} into {schema}")
            gdf = gpd.read_file(file, layer=layer, bbox=gdf_envelope)

            epsg = config.epsg
            gdf.to_crs(epsg=epsg, inplace=True)

            name = layer.replace("_bdlm", "")
            gdf.to_postgis(name, engine, if_exists='append', schema=schema, index=False)
            gdf.to_file(os.path.join(processed_path, os.path.basename(file)), layer=name, driver="GPKG")
