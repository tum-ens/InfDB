import os
import psycopg2
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sqlalchemy
from . import config
from zipfile import ZipFile, BadZipFile
import geopandas as gpd
import chardet
from urllib.parse import urlparse
import subprocess

import logging

log = logging.getLogger(__name__)

def if_multiproccesing():
    status = config.get_value(["loader", "multiproccesing"])
    if status == "active":
        return True
    else:
        return False

def if_active(service):
    status = config.get_value(["loader", "sources", service, "status"])
    if status == "active":
        log.info(f"Loading {service} data...")
        return True
    else:
        log.info("{service} skips, status not active")
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


import os
import requests
from tqdm import tqdm
import logging

log = logging.getLogger(__name__)

def download_files(urls, base_path, chunk_size=1024):
    os.makedirs(base_path, exist_ok=True)
    files = []

    if isinstance(urls, str):
        urls = [urls]

    for url in urls:
        # ToDo Mulitprocessing with Pools as in census2022.py
        filename = url.split("/")[-1]
        path_file = os.path.join(base_path, filename)

        if os.path.exists(path_file):
            log.info(f"File {path_file} already exists.")
        else:
            log.info(f"File {path_file} will be downloaded from {url}")

            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))

                with open(path_file, "wb") as file, tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    desc=filename,
                    disable=(total_size == 0)
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:  # filter out keep-alive chunks
                            file.write(chunk)
                            pbar.update(len(chunk))

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
        parameters = get_db_parameters("citydb")
        host = parameters["host"]
        user = parameters["user"]
        password = parameters["password"]
        db = parameters["db"]
        port = parameters["exposed_port"]

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
        log.debug(f"{query} executed successfully.")

    except Exception as error:
        log.error(f"ProgrammingError: {error}")

def do_cmd(cmd: str):
    log.info(f"Executing command: {cmd}")

    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1  # Zeilenweise Puffern
    )

    # Zeilenweise lesen und direkt loggen
    if process.stdout:
        for line in process.stdout:
            log.info(line.rstrip())

    # Warten bis der Prozess beendet ist
    return_code = process.wait()
    if return_code == 0:
        log.info("Command completed successfully.")
    else:
        log.error(f"Command failed with return code {return_code}")


def import_layers(input_file, layers, schema, prefix="", layer_names=None, scope=True):

    #
    if scope:
        gdf_scope = get_envelop()
    else:
        gdf_scope = None
    epsg = get_db_parameters("citydb")["epsg"]
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

    scope = config.get_value(["loader", "scope"])
    ags_path = config.get_path(["loader", "sources", "bkg", "path", "unzip"])
    log.debug(f"Envelop Path: {ags_path}")
    path = get_file(ags_path, filename="vg5000", ending=".gpkg")
    log.debug(f"Envelop Path: {path}")
    gdf = gpd.read_file(path, layer = "vg5000_gem")

    gdf_scope = gdf[gdf["AGS"].str.startswith(scope)]

    return gdf_scope


def get_db_parameters(service_name: str):

    parameters_loader = config.get_value(["loader", "hosts", service_name])

    # Adopt settings if config-infdb exists
    dict_config = config.get_config()
    if "services" in dict_config:
        parameters = config.get_value(["services", service_name])
        log.debug(f"Using infdb configuration for: {service_name}")

        # Override config-infdb by config-loader
        for key in parameters_loader.keys():
            if parameters_loader[key] != "None":
                parameters[key] = parameters_loader[key]
                log.debug("Key overridden: key = {parameters_loader[key]}")
    else:
        # Use settings from config-loader
        parameters = parameters_loader
        log.debug(f"Using loader configuration for: {service_name}")

    # Check if parameters are found
    for key in parameters.keys():
        if parameters[key] is None:
            log.error(f"Service '{service_name}' not found in configuration.")

    return parameters


def get_db_engine(service_name: str):
    parameters = get_db_parameters(service_name)
    host = parameters["host"]
    user = parameters["user"]
    password = parameters["password"]
    db = parameters["db"]
    port = parameters["exposed_port"]

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


def get_all_files(folder_path, ending):
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
            if filename.lower().endswith(ending):
                csv_files.append(os.path.join(dirpath, filename))
    csv_files.sort()
    return csv_files

def get_file(folder_path, filename, ending):
    files = get_all_files(folder_path, ending)
    # TODO: Check for newest version in case of multiple files
    path = ""
    for file in files:
        if filename in file:
            path = file
            break

    log.debug(f"Envelop Path: {path}")
    return path

def get_website_links(url):

    # HTML-Seite herunterladen
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
        log.info(zip_link)

    return zip_links


def get_file_from_url(url):
    # Extract filename from url
    path = urlparse(url).path
    filename = os.path.basename(path)
    name, extension = os.path.splitext(filename)
    return filename, name, extension