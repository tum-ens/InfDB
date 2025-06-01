import os
import psycopg2
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from src.core import config
from src.core.config import citydb_engine


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
            dbname=config.citydb_db,
            user=config.citydb_user,
            password=config.citydb_password,
            host=config.citydb_host,
            port=config.citydb_port
        )
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
    return citydb_engine


def do_cmd(cmd):
    os.system(cmd)
    print(f"{cmd} executed successfully.")
