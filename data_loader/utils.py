import os
import psycopg2
from sqlalchemy import create_engine
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from CONFIG import config


# CityDB Configuration
citydb_user = config["citydb"]["user"]
citydb_password = config["citydb"]["password"]
citydb_host = config["citydb"]["host_data_import"]  # change this to CITYDB_HOST if you want to run locally not in the container
citydb_port = config["citydb"]["port_data_import"]  # change this to CITYDB_PORT if you want to run locally not in the container
citydb_db = config["citydb"]["db"]
epsg = config["citydb"]["epsg"]


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
    files = []
    for url in urls:
        path_file = os.path.join(base_path, url.split("/")[-1])
        if os.path.exists(path_file):
            print(f"File {path_file} already exists.")
        else:
            # Datei herunterladen
            print(f"File {path_file} will be downloaded from {url}")

            response = requests.get(url)
            with open(path_file, "wb") as file:
                file.write(response.content)
            print(f"{path_file} downloaded.")
        files.append(path_file)
    return files


def sql_query(query):
    try:
        # Connect to the PostgreSQL database-data-import-container
        connection = psycopg2.connect(
            dbname=citydb_db,
            user=citydb_user,
            password=citydb_password,
            host=citydb_host,
            port=citydb_port
        )
        print("here")
        cursor = connection.cursor()
        # # Create the users table
        cursor.execute(query)
        connection.commit()

        # Close the connection
        cursor.close()
        connection.close()
        print(f"{query} executed successfully.")

    except Exception as error:
        print(f"ProgrammingError: {error}")


def get_engine():
    user = citydb_user
    password = citydb_password
    host = citydb_host
    port = citydb_port
    dbname = citydb_db

    db_connection_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    engine = create_engine(db_connection_url)

    return engine


def do_cmd(cmd):
    os.system(cmd)
    print(f"{cmd} executed successfully.")