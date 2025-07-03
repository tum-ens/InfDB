import requests
from bs4 import BeautifulSoup
import os
from zipfile import ZipFile
import geopandas as gpd
import pandas as pd
from src.services.loader import utils, logger
from src.core import config

log = logger.get_logger("infdb-loader")

def get_zensus_links():
    # HTML-Seite herunterladen

    url = config.get_value(["loader", "sources", "zensus_2022", "url"])

    response = requests.get(url)
    html_content = response.content

    # HTML-Seite parsen
    soup = BeautifulSoup(html_content, 'html.parser')

    # Alle Links zu ZIP-Dateien finden
    zip_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.endswith('.zip'):
            zip_links.append(href)

    # Gefundene Links ausgeben
    for zip_link in zip_links:
        print(zip_link)

    return zip_links

# def download_zensus(zip_links):
#
#     os.makedirs(zip_path, exist_ok=True)
#
#     # Dateien herunterladen und entpacken
#     for url in zip_links:
#         # Dateiname aus URL extrahieren
#         filename = os.path.join(zip_path, url.split("/")[-1])
#         # print(f"Downloading {filename}")
#         if os.path.exists(filename):
#             print(f"File {filename} already exists.")
#             continue
#
#         # Datei herunterladen
#         response = requests.get(url)
#         with open(filename, "wb") as file:
#             file.write(response.content)
#         log.info(f"{filename} downloaded.")
#
#     return zip_path

# def unzip_zensus():
#     zip_path = config.get_path(["loader", "sources", "zensus_2022", "path", "zip"])
#     unzip_path = config.get_path(["loader", "sources", "zensus_2022", "path", "unzip"])
#     os.makedirs(unzip_path, exist_ok=True)
#
#     # Unzip downloaded files
#     zip_files = os.listdir(zip_path)
#     for zip_file in zip_files:
#         file_path = os.path.join(zip_path, zip_file)
#         # ZIP-Datei entpacken
#         with ZipFile(file_path, 'r') as zip_ref:
#             zip_ref.extractall(unzip_path)
#
#         log.info(f"{zip_file} unziped.")


def process_census():
    input_path = config.get_path(["loader", "sources", "zensus_2022", "path", "unzip"])
    output_path = config.get_path(["loader", "sources", "zensus_2022", "path", "processed"])
    processed_path = config.get_path(["loader", "sources", "zensus_2022", "path", "processed"])

    # path_root = "../../"

    os.makedirs(output_path, exist_ok=True)

    # Create schema if it doesn't exist
    schema = config.get_value(["loader", "sources", "zensus_2022", "schema"])
    sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"
    utils.sql_query(sql)

    # Create a database-data-import-container connection
    engine = utils.get_db_engine("citydb")

    # Get envelope
    #sql = "SELECT geometry as geom FROM general.envelope"
    gdf_envelope = utils.get_envelop()

    resolutions = config.get_value(["loader", "sources", "zensus_2022", "resolutions"])
    for resolution in resolutions:

        # Get grid within envelope
        grid_file = os.path.join(processed_path, f"DE_Grid_ETRS89-LAEA_{resolution}.gpkg")
        gdf_grid = gpd.read_file(grid_file, bbox=gdf_envelope)

        epsg = config.get_value(["services", "citydb", "epsg"])
        gdf_grid.to_crs(epsg=epsg, inplace=True)

        # gdf_grid.to_file("grid-box.gpkg")
        # gdf_grid["geometry"] = gpd.points_from_xy(gdf_grid.loc[:, "x_mp"], gdf_grid.loc[:, "y_mp"])
        # gdf_grid.to_file("grid-point.gpkg")
        gdf_grid = gdf_grid[["id", "x_mp", "y_mp", "geometry"]]

        print(f"Processing {resolution}...")

        files_with_resolution = [file for file in os.listdir(input_path) if resolution in file]
        for file in files_with_resolution:

            print(file)
            try:
                df = pd.read_csv(os.path.join(input_path, file), sep=";", decimal=",", na_values="–", low_memory=False, encoding='utf-8')  # , encoding="latin_1"   # GeoDataFrame laden (Beispiel) nrows=10,
                df.fillna(0, inplace=True)
                df.columns = df.columns.str.lower()

                gdf_merged = gdf_grid.merge(df, how="left", left_on=["x_mp", "y_mp"], right_on=["x_mp_" + resolution, "y_mp_" + resolution])    # or: how="inner"
                # gdf_merged.drop(["x_mp", "y_mp"], axis=1, inplace=True)
                gdf_merged.drop(["x_mp_" + resolution, "y_mp_" + resolution], axis=1, inplace=True)

                file = file.lower().replace(f"_{resolution}-gitter.csv", "").replace("zensus2022_", "")
                gdf_merged.to_postgis(file, engine, if_exists='replace', schema=schema, index=False)
                gdf_merged.to_file(os.path.join(output_path, f"zenus-2022{resolution}.gpkg"), layer=file, driver="GPKG")

            except Exception as err:
                log.info(Exception, err)
                log.info(file)

    log.info("Zensus2022 imported successfully.")


def load():
    if not utils.if_active("zensus_2022"):
        log.info("zensus_2022 skips, status not active")
        return

    zip_links = get_zensus_links()

    #download_zensus(zip_links)
    zip_path = config.get_path(["loader", "sources", "zensus_2022", "path", "zip"])
    utils.download_files(zip_links, zip_path)

    #zip_path = config.get_path(["loader", "sources", "zensus_2022", "path", "zip"])
    unzip_path = config.get_path(["loader", "sources", "zensus_2022", "path", "unzip"])

    zip_files = [os.path.join(zip_path, f) for f in os.listdir(zip_path)]
    utils.unzip(zip_files, unzip_path)

    process_census()
