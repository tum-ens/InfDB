import os
import subprocess
import requests
import multiprocessing
import chardet
from zipfile import ZipFile, BadZipFile
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sqlalchemy
import psycopg2
import geopandas as gpd
from urllib.parse import urlparse
from . import config
from pySmartDL import SmartDL
import logging


log = logging.getLogger(__name__)


def if_multiproccesing():
    status = config.get_value(["loader", "multiproccesing", "status"])
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
    soup = BeautifulSoup(html_content, "html.parser")

    # Alle Links zu ZIP-Dateien finden
    zip_links = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.endswith(ending):
            # Check for filters
            if filter in href.lower():
                # Append if url not already in list
                full_url = urljoin(url, link["href"])
                if full_url not in zip_links:
                    zip_links.append(full_url)

    # Gefundene Links ausgeben
    log.debug(zip_links)

    return zip_links


def download_files(urls, base_path):
    if os.path.isdir(base_path):
        os.makedirs(base_path, exist_ok=True)

    if isinstance(urls, str):
        urls = [urls]
    
    objs = []
    for url in urls:
        obj = SmartDL(url, base_path, progress_bar=True)
        target_path = obj.get_dest()
        if os.path.exists(target_path):
            log.info(f"File {target_path} already exists.")
        else:
            log.info(f"File {target_path} downloading ...")
            obj.start(blocking=False)   # non-blocking start
            objs.append(obj)

    # Wait for all to finish
    files = []
    for obj in objs:
        obj.wait()
        files.append(obj.get_dest())

    return files


def unzip(zip_files, unzip_dir):
    os.makedirs(unzip_dir, exist_ok=True)

    if isinstance(zip_files, str):
        zip_files = [zip_files]

    for zip_file in zip_files:
        try:
            with ZipFile(zip_file, "r") as zip_ref:
                members = zip_ref.namelist()
                # Check if all files already exist
                all_exist = all(
                    os.path.exists(os.path.join(unzip_dir, member))
                    for member in members
                )

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
            dbname=db, user=user, password=password, host=host, port=port
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
        bufsize=1,  # Zeilenweise Puffern
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
        gdf = gpd.read_file(input_file, layer=layer, mask=gdf_scope)
        gdf.to_crs(epsg=epsg, inplace=True)
        # gdf.to_file(output_file, layer=layer, driver="GPKG")
        gdf.to_postgis(
            layer_name, citydb_engine, if_exists="replace", schema=schema, index=False
        )


def get_envelop():
    scope = config.get_list(["loader", "scope"])
    ags_path = config.get_path(["loader", "sources", "bkg", "path", "unzip"])
    log.debug(f"Envelop Path: {ags_path}")
    path = get_file(ags_path, filename="vg5000", ending=".gpkg")
    log.debug(f"Envelop Path: {path}")
    gdf = gpd.read_file(path, layer="vg5000_gem")

    gdf_scope = gdf[gdf["AGS"].str.startswith(tuple(scope))]

    return gdf_scope


def get_db_parameters(service_name: str):
    parameters_loader = config.get_value(["loader", "hosts", service_name])

    # Adopt settings if config-infdb exists
    dict_config = config.get_config()
    if "services" in dict_config:
        parameters = config.get_value(["services", service_name])
        log.debug(f"Using infdb configuration for: {service_name}")

        # Override config-infdb by config-loader
        keys = parameters_loader.keys()
        for key in keys:
            if key == "host":
                parameters[key] = "host.docker.internal"  # default to localhost

            if parameters_loader[key] != "None":
                parameters[key] = parameters_loader[key]
                log.debug(f"Key overridden: key = {parameters_loader[key]}")
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
    with open(filepath, "rb") as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        source_encoding = result["encoding"]

    if source_encoding is None:
        raise ValueError(f"Could not detect encoding of file: {filepath}")

    if source_encoding.lower() != "utf-8":
        # Re-encode the file to UTF-8
        log.info(f"Re-encoding file from {source_encoding} to UTF-8: {filepath}")
        temp_path = filepath + "_utf8.csv"
        with (
            open(filepath, "r", encoding=source_encoding, errors="replace") as src,
            open(temp_path, "w", encoding="utf-8") as dst,
        ):
            for line in src:
                dst.write(line)
        return temp_path

    return filepath  # already UTF-8


def get_all_files(folder_path, ending):
    """
    Recursively finds all ending files in the given folder and its subfolders.

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
    """
    Recursively finds all ending files in the given folder and its subfolders.

    Parameters:
        folder_path (str): Path to the top-level folder.

    Returns:
        List[str]: List of full paths to .csv files.
    """
    files = get_all_files(folder_path, ending)

    # Filter files that contain the filename
    matching_files = [f for f in files if filename.lower() in f.lower()]

    if not matching_files:
        log.error(
            f"No files found containing '{filename}' with ending '{ending}' in {folder_path}"
        )
        return None

    # Pick the newest by modification time
    newest_file = max(matching_files, key=os.path.getmtime)

    log.debug(f"Envelop Path: {newest_file}")
    return newest_file


def get_website_links(url):
    # HTML-Seite herunterladen
    response = requests.get(url)
    html_content = response.content

    # HTML-Seite parsen
    soup = BeautifulSoup(html_content, "html.parser")

    # Alle Links zu ZIP-Dateien finden
    zip_links = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.endswith(".zip"):
            zip_links.append(href)

    # Gefundene Links ausgeben
    for zip_link in zip_links:
        log.debug(zip_link)

    return zip_links


def get_file_from_url(url):
    # Extract filename from url
    path = urlparse(url).path
    filename = os.path.basename(path)
    name, extension = os.path.splitext(filename)
    return filename, name, extension


def get_number_processes():
    """
    Get the maximum number of processes to use based on the configuration.
    """
    number_processes = 1
    max_processes = config.get_value(["loader", "multiproccesing", "max_cores"])

    if config.get_value(["loader", "multiproccesing", "status"]) == "active":
        number_processes = min(multiprocessing.cpu_count(), max_processes)

    log.debug(
        f"Max processes: {max_processes}, Number of processes: {number_processes}"
    )

    return number_processes
