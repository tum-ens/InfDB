import os
import pandas as pd
import geopandas as gpd
from sqlalchemy import text
from src.core import config

SCHEMA = "sunpot"
INPUT_DIR = config.get_value(["base", "base_sunset_dir"])
engine = config.get_db_engine("citydb")


def import_to_v5():
    os.makedirs(INPUT_DIR, exist_ok=True)

    create_schema_sql = text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}";')
    run_query(create_schema_sql)
    for filename in os.listdir(INPUT_DIR):
        table_name = filename.split(".")[0]
        csv_path = os.path.join(INPUT_DIR, filename)

        print(f"Importing table '{table_name}'")

        df = pd.read_csv(csv_path)
        geometry_cols = [col for col in df.columns if col.lower().startswith("geom")]
        if geometry_cols:
            for col in geometry_cols:
                df[col] = gpd.GeoSeries.from_wkt(df[col])

            gdf = gpd.GeoDataFrame(df, geometry=geometry_cols[0], crs=f"EPSG:{config.get_value(['services', 'citydb', 'epsg'])}")
            gdf.to_postgis(table_name, engine, schema=SCHEMA, if_exists="replace", index=False)
        else:
            df.to_sql(table_name, engine, schema=SCHEMA, if_exists="replace", index=False)

        print(f"Imported {len(df)} rows into '{SCHEMA}.{table_name}'")


def run_query(query: str):
    with engine.begin() as conn:
        conn.execute(query)
