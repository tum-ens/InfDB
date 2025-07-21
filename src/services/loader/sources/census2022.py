import requests
from bs4 import BeautifulSoup
import os
import geopandas as gpd
import pandas as pd
from src.services.loader import utils, logger
from src.core import config

log = logger.get_logger("infdb-loader")


def get_zensus_links():
    url = config.get_value(["loader", "sources", "zensus_2022", "url"])

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


def process_census():
    input_path = config.get_path(["loader", "sources", "zensus_2022", "path", "unzip"])

    # output_path = config.get_path(["loader", "sources", "zensus_2022", "path", "processed"])
    # os.makedirs(output_path, exist_ok=True)

    # Create schema if it doesn't exist
    schema = config.get_value(["loader", "sources", "zensus_2022", "schema"])
    sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"
    utils.sql_query(sql)

    # Create a database-data-import-container connection
    engine = utils.get_db_engine("citydb")

    # Get envelope
    gdf_envelope = utils.get_envelop()

    replace_dict = {"gebaeude": "gbd",
                    "wohnbevoelkerung": "wbe",
                    "wohnraum": "wrm",
                    "haushalte": "hht",
                    "heizungsart": "hzat",
                    "ueberwiegend": "ubwer",
                    "anzahl": "anz",
                    "anteil": "atl",
                    "unter": "utr",
                    "flache": "fle",
                    "wohnungen": "wogen",
                    "nettokaltmiete": "nkm",
                    "durschnittliche": "durtle",
                    "energietraeger": "etrg",
                    "heizung": "heiz",
                    "staatsangehoerigkeiten": "stagktn",

                    }
    # Get user configurations
    layers = config.get_value(["loader", "sources", "zensus_2022", "layer"])
    prefix = config.get_value(["loader", "sources", "zensus_2022", "prefix"])
    schema = config.get_value(["loader", "sources", "zensus_2022", "schema"])

    resolutions = config.get_value(["loader", "sources", "zensus_2022", "resolutions"])
    csv_files = utils.get_all_files(input_path, ".csv")
    # for file in csv_files:
    #     print(os.path.basename(file))

    for resolution in resolutions:

        log.info(f"Processing {resolution}...")
        for file in csv_files:
            # print(file)
            if "_utf8.csv" in file:
                print("utf8" + file)
                continue
            if resolution not in file:
                continue
            # if os.path.basename(file).replace("_" + resolution, "") not in layers:
            #     log.info(f"Skipping {file}...")
            #     continue

            log.info(f"Processing {file}...")
            try:
                csv_path = os.path.join(input_path, file)
                csv_path = utils.ensure_utf8_encoding(csv_path)  # <-- check and fix encoding
                df = pd.read_csv(csv_path, sep=";", decimal=",", na_values="–", low_memory=False, encoding='utf-8')  # , encoding="latin_1"   # GeoDataFrame laden (Beispiel) nrows=10,

                df.fillna(0, inplace=True)
                df.columns = df.columns.str.lower()

                gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.loc[:, "x_mp_" + resolution], df.loc[:, "y_mp_" + resolution]), crs="EPSG:3035")  # ETRS89 / UTM zone 32N
                epsg = config.get_value(["services", "citydb", "epsg"])
                gdf = gdf.to_crs(epsg=epsg)
                if not gdf_envelope.empty:
                    gdf_clipped = gpd.clip(gdf, gdf_envelope)
                else:
                    gdf_clipped = gdf

                table_name = os.path.basename(file).lower().replace(f"_{resolution}-gitter.csv", "").replace("zensus2022_", "")
                for key, value in replace_dict.items():
                    table_name = table_name.replace(key, value)
                table_name = prefix + "_" + resolution + "_" + table_name
                gdf_clipped.to_postgis(table_name, engine, if_exists='replace', schema=schema, index=False)
                # gdf_clipped.to_file(os.path.join(output_path, f"zenus-2022{resolution}.gpkg"), layer=file, driver="GPKG")

            except Exception as err:
                log.info(Exception, err)
                log.info(file)

    log.info("Zensus2022 imported successfully.")


def load():
    logger.init_logger("infdb-loader", "infdb-loader.log")
    log = logger.get_logger("infdb-loader")

    if not utils.if_active("zensus_2022"):
        log.info("zensus_2022 skips, status not active")
        return

    zip_links = get_zensus_links()

    # download_zensus(zip_links)
    zip_path = config.get_path(["loader", "sources", "zensus_2022", "path", "zip"])
    utils.download_files(zip_links, zip_path)

    unzip_path = config.get_path(["loader", "sources", "zensus_2022", "path", "unzip"])

    zip_files = [os.path.join(zip_path, f) for f in os.listdir(zip_path)]
    utils.unzip(zip_files, unzip_path)

    process_census()
