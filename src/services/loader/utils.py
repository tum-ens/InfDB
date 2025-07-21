import os
import psycopg2
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sqlalchemy
from src.core import config
from zipfile import ZipFile, BadZipFile
from src.services.loader import logger
import geopandas as gpd
import chardet

log = logger.get_logger("infdb-loader")


def if_active(service):
    status = config.get_value(["loader", "sources", service, "status"])
    if status == "active":
        return True
    else:
        return False


def any_element_in_string(target_string, elements):
    return any(element in target_string for element in elements)


def get_links(url, ending, filter):
    response = requests.get(url)
    html_content = response.content

    # HTML-Seite parsen
    soup = BeautifulSoup(html_content, 'html.parser')

    # Alle Links zu ZIP-Dateien finden
    zip_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.endswith(ending):
            # Check for filters
            if any_element_in_string(href.lower(), filter):
                # Append if url not already in list
                full_url = urljoin(url, link['href'])
                if full_url not in zip_links:
                    zip_links.append(full_url)

    # Gefundene Links ausgeben
    print(zip_links)

    return zip_links


def download_files(urls, base_path):
    os.makedirs(base_path, exist_ok=True)
    files = []
    # if urls is a string, convert it to a list
    if isinstance(urls, str):
        urls = [urls]

    for url in urls:
        path_file = os.path.join(base_path, url.split("/")[-1])
        if os.path.exists(path_file):
            log.info(f"File {path_file} already exists.")
        else:
            # Datei herunterladen
            log.info(f"File {path_file} will be downloaded from {url}")

            response = requests.get(url)
            with open(path_file, "wb") as file:
                file.write(response.content)
            log.info(f"{path_file} downloaded.")
        files.append(path_file)
    return files


def unzip(zip_files, unzip_dir):
    os.makedirs(unzip_dir, exist_ok=True)

    for zip_file in zip_files:
        try:
            with ZipFile(zip_file, 'r') as zip_ref:
                members = zip_ref.namelist()
                # Check if all files already exist
                all_exist = all(os.path.exists(os.path.join(unzip_dir, member)) for member in members)

                if all_exist:
                    log.info(f"Skipping {zip_file} — all files already extracted.")
                    continue

                log.info(f"Unzipping {zip_file}")
                zip_ref.extractall(unzip_dir)
        except BadZipFile as e:
            log.error(f"Error unzipping {zip_file}: {e}")


def sql_query(query):
    try:
        # Connect to the PostgreSQL database-data-import-container
        host, port, user, password, db = get_db_config("citydb")
        connection = psycopg2.connect(
            dbname=db,
            user=user,
            password=password,
            host=host,
            port=port
        )
        cursor = connection.cursor()
        # # Create the users table
        cursor.execute(query)
        connection.commit()

        # Close the connection
        cursor.close()
        connection.close()
        log.info(f"{query} executed successfully.")

    except Exception as error:
        log.info(f"ProgrammingError: {error}")


def do_cmd(cmd):
    os.system(cmd)
    print(f"{cmd} executed successfully.")


def import_layers(input_file, layers, schema, prefix="", layer_names=None):

    gdf_scope = get_envelop()
    epsg = config.get_value(["services", "citydb", "epsg"])
    citydb_engine = get_db_engine("citydb")

    if layer_names is None:
        layer_names = layers

    # Add prefix
    if prefix:
        layer_names = [prefix + "_" + name for name in layer_names]

    for layer, layer_name in zip(layers, layer_names):
        log.info(f"Importing layer: {layer} into {schema}")
        gdf = gpd.read_file(input_file, layer=layer, bbox=gdf_scope)
        gdf.to_crs(epsg=epsg, inplace=True)
        # gdf.to_file(output_file, layer=layer, driver="GPKG")
        gdf.to_postgis(layer_name, citydb_engine, if_exists='replace', schema=schema, index=False)


def get_envelop():

    # # Get envelope from the database
    # engine = get_engine()
    # sql = "SELECT geometry as geom FROM general.envelope"
    # gdf_envelope = gpd.read_postgis(sql, engine)

    scope = config.get_value(["base", "scope"])
    nuts_path = config.get_value(["loader", "sources", "bkg", "path", "unzip"])
    gdf = gpd.read_file(os.path.join(config.get_root_path(), os.path.join(nuts_path, "nuts250_12-31.utm32s.gpkg/nuts250_1231/DE_NUTS250.gpkg")))

    gdf_scope = gdf[gdf["NUTS_CODE"].str.startswith(scope)]

    return gdf_scope


def get_db_config(service_name: str):
    parameters = config.get_value(["loader", "hosts", service_name])
    if not parameters:
        raise ValueError(f"Service '{service_name}' not found in configuration.")

    host = parameters["host"]
    user = parameters["user"]
    password = parameters["password"]
    db = parameters["db"]
    port = parameters["port"]

    return host, port, user, password, db


def get_db_engine(service_name: str):
    host, port, user, password, db = get_db_config(service_name)
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    engine = sqlalchemy.create_engine(db_url)

    return engine


def ensure_utf8_encoding(filepath: str) -> str:
    with open(filepath, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        source_encoding = result['encoding']

    if source_encoding is None:
        raise ValueError(f"Could not detect encoding of file: {filepath}")

    if source_encoding.lower() != 'utf-8':
        # Re-encode the file to UTF-8
        log.info(f"Re-encoding file from {source_encoding} to UTF-8: {filepath}")
        temp_path = filepath + "_utf8.csv"
        with open(filepath, 'r', encoding=source_encoding, errors='replace') as src, \
             open(temp_path, 'w', encoding='utf-8') as dst:
            for line in src:
                dst.write(line)
        return temp_path

    return filepath  # already UTF-8


def get_all_csv_files(folder_path):
    """
    Recursively finds all .csv files in the given folder and its subfolders.

    Parameters:
        folder_path (str): Path to the top-level folder.

    Returns:
        List[str]: List of full paths to .csv files.
    """
    csv_files = []
    for dirpath, _, filenames in os.walk(folder_path):
        for filename in filenames:
            if filename.lower().endswith(".csv"):
                csv_files.append(os.path.join(dirpath, filename))
    csv_files.sort()
    return csv_files
