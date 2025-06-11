import os
import geopandas as gpd

from data_import.imp import config, utils


def import_basemap():

    # Create a database-data-import-container connection
    engine = utils.get_engine()

    # Get envelope
    sql = "SELECT geometry as geom FROM general.envelope"
    gdf_envelope = gpd.read_postgis(sql, engine)

    base_path = config.get_path(["opendata", "basemap", "basemap_dir"])
    processed_path = config.get_path(["opendata", "basemap", "basemap_processed_dir"])
    os.makedirs(base_path, exist_ok=True)
    os.makedirs(processed_path, exist_ok=True)

    site_url = config.get_value(["opendata", "basemap", "url"])
    ending = config.get_value(["opendata", "basemap", "ending"])
    filter = config.get_value(["opendata", "basemap", "filter"])
    urls = utils.get_links(site_url, ending, filter)

    download_files = utils.download_files(urls, base_path)

    schema = config.get_value(["opendata", "basemap", "schema"])
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


import_basemap()
