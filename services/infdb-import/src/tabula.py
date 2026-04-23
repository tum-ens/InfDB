import json
import os
import sys
from typing import Any, Dict, List

import pandas as pd
from infdb import InfDB
from sqlalchemy import text

from . import utils

# ============================== Constants ==============================
FILE_ENCODING: str = "utf-8"
JSON_EXT: str = ".json"
CSV_EXT: str = ".csv"


def load(infdb: InfDB) -> bool:
    """Downloads Tabula JSONs, transforms them to CSV, and loads into Postgres.

    Behavior preserved:
    - Skips entirely when `tabula` feature flag is inactive.
    - Downloads from configured URLs and writes CSVs to the base path.
    - Ensures the target schema then writes tables with `if_exists='replace'`.
    """
    log = infdb.get_worker_logger()
    TOOL_NAME = infdb.get_toolname()
    try:
        if not utils.if_active("tabula", infdb):
            return True

        base_path = infdb.get_config_path([TOOL_NAME, "sources", "tabula", "path", "base"], type="loader")
        os.makedirs(base_path, exist_ok=True)

        urls: List[str] = infdb.get_config_value([TOOL_NAME, "sources", "tabula", "url"])
        utils.download_files(urls, base_path, infdb)

        material_path = utils.get_file(base_path, "material", JSON_EXT, infdb)
        type_elements_path = utils.get_file(base_path, "TypeElements", JSON_EXT, infdb)

        # --- Load JSON files ---
        with open(type_elements_path, "r", encoding=FILE_ENCODING) as f:
            type_elements: Dict[str, Any] = json.load(f)

        with open(material_path, "r", encoding=FILE_ENCODING) as f:
            materials: Dict[str, Any] = json.load(f)

        # --- Process materials ---
        df_materials = pd.DataFrame.from_dict(materials, orient="index").reset_index()
        df_materials.rename(columns={"index": "material_id"}, inplace=True)

        # --- Extract TypeElements + layers ---
        element_records: List[Dict[str, Any]] = []
        layer_records: List[Dict[str, Any]] = []
        next_element_id = 0

        for name, data in type_elements.items():
            base_name = name.split("_")[0]
            element_id = next_element_id
            next_element_id += 1

            # building_age_group example: [start, end]
            start_year, end_year = (None, None)
            building_age_group = data.get("building_age_group")
            if isinstance(building_age_group, list) and len(building_age_group) >= 2:
                start_year, end_year = building_age_group[0], building_age_group[1]

            element_records.append(
                {
                    "element_id": element_id,
                    "element_name": base_name,
                    "construction_data": data.get("construction_data"),
                    "inner_radiation": data.get("inner_radiation"),
                    "inner_convection": data.get("inner_convection"),
                    "outer_radiation": data.get("outer_radiation"),
                    "outer_convection": data.get("outer_convection"),
                    "start_year": start_year,
                    "end_year": end_year,
                }
            )

            for layer_index, layer in data["layer"].items():
                layer_records.append(
                    {
                        "element_id": element_id,
                        "material_id": layer["material"]["material_id"],
                        "layer_index": int(layer_index),
                        "material_name": layer["material"]["name"],
                        "thickness": layer["thickness"],
                    }
                )

        # --- DataFrames ---
        df_elements = pd.DataFrame(element_records)
        df_layers = pd.DataFrame(layer_records)

        # Persist CSVs
        df_elements.to_csv(os.path.join(base_path, "type_elements" + CSV_EXT), index=False)
        df_layers.to_csv(os.path.join(base_path, "layers" + CSV_EXT), index=False)
        df_materials.to_csv(os.path.join(base_path, "materials" + CSV_EXT), index=False)

        # # Ensure schema exists via InfdbClient and grab an engine
        # schema: str = infdb.get_config_value([TOOL_NAME, "sources", "tabula", "schema"])
        # with infdb.connect() as db:
        #     db.execute_query(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
        #     db.execute_query(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        #     engine = db.get_db_engine()

        # Prefix for table names
        prefix: str = infdb.get_config_value([TOOL_NAME, "sources", "tabula", "prefix"])
        schema = infdb.get_config_value([TOOL_NAME, "sources", "tabula", "schema"])
        engine = infdb.get_db_engine()

        # Ensure target schema exists (step 3)
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema};"))
            conn.commit()

        # Export to Postgres
        df_elements.to_sql(f"{prefix}_type_elements", engine, schema=schema, if_exists="replace", index=False)
        df_layers.to_sql(f"{prefix}_layers", engine, schema=schema, if_exists="replace", index=False)
        df_materials.to_sql(f"{prefix}_materials", engine, schema=schema, if_exists="replace", index=False)

        log.info("Tabula data loaded successfully")
        sys.exit(0)
    except Exception as err:
        log.exception("An error occurred while processing TABULA data: %s", str(err))
        sys.exit(1)
