import os
import logging
from . import utils, config, logger
import pandas as pd
import requests

log = logging.getLogger(__name__)

def load(log_queue):
    logger.setup_worker_logger(log_queue)

    if not utils.if_active("tabula"):
        return

    base_path = config.get_path(["loader", "sources", "tabula", "path", "base"])
    os.makedirs(base_path, exist_ok=True)
    
    urls = config.get_value(["loader", "sources", "tabula", "url"])
    files = utils.download_files(urls, base_path)
    
    material_path = utils.get_file(base_path, "material", ".json")
    type_elements_path = utils.get_file(base_path, "TypeElements", ".json")

    import json
    import pandas as pd

    # --- JSON-Dateien laden ---
    with open(type_elements_path, "r") as f:
        type_elements = json.load(f)

    with open(material_path, "r") as f:
        materials = json.load(f)

    # --- Materialdaten verarbeiten ---
    df_materials = pd.DataFrame.from_dict(materials, orient="index").reset_index()
    df_materials.rename(columns={"index": "material_id"}, inplace=True)

    # --- TypeElements + Layer extrahieren ---
    records = []
    layer_records = []
    type_element_id = 0

    for name, data in type_elements.items():
        base_name = name.split("_")[0]
        element_id = type_element_id
        type_element_id += 1

        building_age_group = data.get("building_age_group", [None, None])
        start_year, end_year = building_age_group

        records.append({
            "element_id": element_id,
            "element_name": base_name,
            "construction_data": data.get("construction_data"),
            "inner_radiation": data.get("inner_radiation"),
            "inner_convection": data.get("inner_convection"),
            "outer_radiation": data.get("outer_radiation"),
            "outer_convection": data.get("outer_convection"),
            "start_year": start_year,
            "end_year": end_year
        })

        for layer_index, layer in data["layer"].items():
            layer_records.append({
                "element_id": element_id,
                "material_id": layer["material"]["material_id"],
                "layer_index": int(layer_index),
                "material_name": layer["material"]["name"],
                "thickness": layer["thickness"]
            })

    # --- DataFrames erzeugen ---
    df_elements = pd.DataFrame(records)
    df_layers = pd.DataFrame(layer_records)
    
    df_elements.to_csv(os.path.join(base_path, "type_elements.csv"), index=False)
    df_layers.to_csv(os.path.join(base_path, "layers.csv"), index=False)
    df_materials.to_csv(os.path.join(base_path, "materials.csv"), index=False)

    # --- Ausgabe prüfen (optional) ---
    log.info("=== Materials ===")
    log.info(df_materials.head())

    log.info("\n=== Type Elements ===")
    log.info(df_elements.head())

    log.info("\n=== Layer Mapping ===")
    log.info(df_layers.head())


    # Create schema if it doesn't exist
    schema = config.get_value(["loader", "sources", "tabula", "schema"])
    sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"
    utils.sql_query(sql)

    # Prefix for table names
    prefix = config.get_value(["loader", "sources", "tabula", "prefix"])

    # Create database connection
    citydb_engine = utils.get_db_engine("citydb")
    
    # Export to citdyb
    df_elements.to_sql(f"{prefix}_type_elements", citydb_engine, schema=schema, if_exists="replace", index=False)
    df_layers.to_sql(f"{prefix}__layers", citydb_engine, schema=schema, if_exists="replace", index=False)
    df_materials.to_sql(f"{prefix}_materials", citydb_engine, schema=schema, if_exists="replace", index=False)

    log.info(f"Tabula data loaded successfully")

