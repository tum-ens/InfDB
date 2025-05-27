import requests
from bs4 import BeautifulSoup
import os
from zipfile import ZipFile
import geopandas as gpd
import pandas as pd
from data_loader import utils
from CONFIG import config


def get_zensus_links():
    # HTML-Seite herunterladen

    url = config["opendata"]["zensus_2022"]["url"]

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


def download_zensus(zip_links):
    zip_path = config["opendata"]["zensus_2022"]["zensus_2022_zip_dir"]
    os.makedirs(zip_path, exist_ok=True)

    # Dateien herunterladen und entpacken
    for url in zip_links:
        # Dateiname aus URL extrahieren
        filename = os.path.join(zip_path, url.split("/")[-1])
        # print(f"Downloading {filename}")
        if os.path.exists(filename):
            print(f"File {filename} already exists.")
            continue

        # Datei herunterladen
        response = requests.get(url)
        with open(filename, "wb") as file:
            file.write(response.content)
        print(f"{filename} downloaded.")

    return zip_path


def unzip_zensus():

    zip_path = config["opendata"]["zensus_2022"]["zensus_2022_zip_dir"]
    unzip_path = config["opendata"]["zensus_2022"]["zensus_2022_unzip_dir"]

    os.makedirs(unzip_path, exist_ok=True)

    # Unzip downloaded files
    zip_files = os.listdir(zip_path)
    for zip_file in zip_files:
        file_path = os.path.join(zip_path, zip_file)
        # ZIP-Datei entpacken
        with ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(unzip_path)

        print(f"{zip_file} unziped.")


def process_census():

    input_path = config["opendata"]["zensus_2022"]["zensus_2022_unzip_dir"]
    output_path = config["opendata"]["zensus_2022"]["zensus_2022_processed_dir"]
    processed_path = config["opendata"]["bkg"]["bkg_processed_dir"]

    # path_root = "../../"

    os.makedirs(output_path, exist_ok=True)

    # Create schema if it doesn't exist
    schema = config["opendata"]["zensus_2022"]["schema"]
    sql = f"""
        drop schema if exists {schema} cascade;
        CREATE SCHEMA IF NOT EXISTS {schema};"""
    utils.sql_query(sql)

    # Create a database-data-import-container connection
    engine = utils.get_engine()

    # Get envelope
    sql = "SELECT geometry as geom FROM general.envelope"
    gdf_envelope = gpd.read_postgis(sql, engine)

    resolutions = config["opendata"]["zensus_2022"]["resolutions"]
    for resolution in resolutions:

        # Get grid within envelope
        grid_file = os.path.join(processed_path, f"DE_Grid_ETRS89-LAEA_{resolution}.gpkg")
        gdf_grid = gpd.read_file(grid_file, bbox=gdf_envelope)

        epsg = config.epsg
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
                print(Exception, err)
                print(file)

    print("Zensus2022 imported successfully.")


def import_census2022():
    status = config["opendata"]["zensus_2022"]["status"]
    if status != "active":
        print("zensus_2022 skips, status not active")
        return
    zip_links = get_zensus_links()
    download_zensus(zip_links)
    unzip_zensus()
    process_census()
