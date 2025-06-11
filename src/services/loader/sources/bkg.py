import os
import requests
from zipfile import ZipFile
import geopandas as gpd
from src.services.loader import utils
from src.core import config


def import_bkg():
    status = config.get_value(["loader", "bkg", "status"])
    if status != "active":
        print("bkg skips, status not active")
        return

    # Get locations
    zip_path = config.get_path(["loader", "bkg", "bkg_zip_dir"])
    unzip_path = config.get_path(["loader", "bkg", "bkg_unzip_dir"])
    processed_path = config.get_path(["loader", "bkg", "bkg_processed_dir"])

    os.makedirs(zip_path, exist_ok=True)
    os.makedirs(unzip_path, exist_ok=True)
    os.makedirs(processed_path, exist_ok=True)

    # Create schema if it doesn't exist
    schema = config.get_value(["loader", "bkg", "schema"])
    sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"
    utils.sql_query(sql)

    def download_and_unzip(url, zip_path, unzip_dir):
        if not os.path.exists(zip_path):
            print(f"Downloading {zip_path}")
            response = requests.get(url)
            with open(zip_path, "wb") as file:
                file.write(response.content)
        else:
            print(f"{zip_path} already exists.")

        with ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(unzip_dir)

    def import_layers(gpkg_file, layers):
        # Get envelope
        engine = utils.get_engine()
        sql = "SELECT geometry as geom FROM general.envelope"
        gdf_envelope = gpd.read_postgis(sql, engine)

        processed_file = os.path.join(processed_path, os.path.basename(gpkg_file))

        input_file = gpkg_file
        output_file = processed_file
        minX, minY, maxX, maxY = gdf_envelope.total_bounds
        # cmd = f"ogr2ogr -f \"GPKG\" {output_file} {input_file} -spat {minX} {minY} {maxX} {maxY}"
        # utils.do_cmd(cmd)

        for layer in layers:
            print(f"Importing layer: {layer} into {schema}")
            gdf = gpd.read_file(input_file, layer=layer, bbox=(minX, minY, maxX, maxY))

            epsg = config.get_value(["services", "citydb", "epsg"])
            gdf.to_crs(epsg=epsg, inplace=True)

            gdf.to_file(output_file, layer=layer, driver="GPKG")
            gdf.to_postgis(layer, engine, if_exists='replace', schema=schema, index=False)

            # subprocess.run([
            #     "ogr2ogr", "-f", "PostgreSQL", pg_conn,
            #     "-t_srs", f"epsg:{config.epsg}", "-overwrite", "-clipsrclayer", layer,
            #     processed_file, layer
            # ])

    # Verwaltungsgebiete
    print("Downloading and unzipping Verwaltungsgebiete")
    vg_zip = os.path.join(zip_path, "vg5000.utm32s.gpkg.ebenen.zip")
    download_and_unzip("https://daten.gdz.bkg.bund.de/produkte/vg/vg5000_1231/aktuell/vg5000_12-31.utm32s.gpkg.ebenen.zip",
                       vg_zip, unzip_path)

    vg_gpkg = os.path.join(unzip_path, "vg5000_12-31.utm32s.gpkg.ebenen/vg5000_ebenen_1231/DE_VG5000.gpkg")
    vg_layers = ["vg5000_gem", "vg5000_krs", "vg5000_lan", "vg5000_li", "vg5000_rbz", "vg5000_sta", "vg5000_vwg"]
    import_layers(vg_gpkg, vg_layers)

    # NUTS-Gebiete
    print("Downloading and unzipping NUTS-Gebiete")
    nuts_zip = os.path.join(zip_path, "nuts250.utm32s.gpkg.zip")
    download_and_unzip("https://daten.gdz.bkg.bund.de/produkte/vg/nuts250_1231/aktuell/nuts250_12-31.utm32s.gpkg.zip",
                       nuts_zip, unzip_path)

    nuts_gpkg = os.path.join(unzip_path, "nuts250_12-31.utm32s.gpkg/nuts250_1231/DE_NUTS250.gpkg")
    nuts_layers = ["nuts250_n1", "nuts250_n2", "nuts250_n3"]
    import_layers(nuts_gpkg, nuts_layers)

    # Geogitter
    # ToDo: loop for resolution
    # 1km
    print("Downloading and unzipping Geogitter")
    geogitter_zip = os.path.join(zip_path, "DE_Grid_ETRS89-LAEA_1km.gpkg.zip")
    download_and_unzip("https://daten.gdz.bkg.bund.de/produkte/sonstige/geogitter/aktuell/DE_Grid_ETRS89-LAEA_1km.gpkg.zip",
                       geogitter_zip, unzip_path)

    geogitter_1km_gpkg = os.path.join(unzip_path, "DE_Grid_ETRS89-LAEA_1km.gpkg/geogitter/DE_Grid_ETRS89-LAEA_1km.gpkg")
    geogitter_1km_layers = ["de_grid_laea_1km"]
    import_layers(geogitter_1km_gpkg, geogitter_1km_layers)

    # 10km
    geogitter_zip = os.path.join(zip_path, "DE_Grid_ETRS89-LAEA_10km.gpkg.zip")
    download_and_unzip("https://daten.gdz.bkg.bund.de/produkte/sonstige/geogitter/aktuell/DE_Grid_ETRS89-LAEA_10km.gpkg.zip",
                       geogitter_zip, unzip_path)

    geogitter_10km_gpkg = os.path.join(unzip_path, "DE_Grid_ETRS89-LAEA_10km.gpkg/geogitter/DE_Grid_ETRS89-LAEA_10km.gpkg")
    geogitter_10km_layers = ["de_grid_laea_10km"]
    import_layers(geogitter_10km_gpkg, geogitter_10km_layers)

    # 100m
    # geogitter_zip = os.path.join(zip_path, "DE_Grid_ETRS89-LAEA_100m.gpkg.zip")
    # download_and_unzip("https://daten.gdz.bkg.bund.de/produkte/sonstige/geogitter/aktuell/DE_Grid_ETRS89-LAEA_100m.gpkg.zip",
    #                    geogitter_zip, unzip_path)

    # geogitter_100m_gpkg = os.path.join(unzip_path, "DE_Grid_ETRS89-LAEA_100m/geogitter/DE_Grid_ETRS89-LAEA_100m.gpkg")
    # geogitter_100m_layers = ["de_grid_laea_100m"]
    # import_layers(geogitter_100m_gpkg, geogitter_100m_layers)

    # ToDo: Remove temporary files
