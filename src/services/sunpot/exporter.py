import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from src.core import config

load_dotenv()
CITYDBV4_DB = os.getenv("CITYDBV4_DB")
CITYDBV4_USER = os.getenv("CITYDBV4_USER")
CITYDBV4_PASSWORD = os.getenv("CITYDBV4_PASSWORD")
CITYDBV4_HOST = os.getenv("CITYDBV4_HOST")
CITYDBV4_PORT = os.getenv("CITYDBV4_PORT", "5432")

SCHEMA = "sunpot"
OUTPUT_DIR = config.get_value(["base", "base_sunset_dir"])


def export_to_csv():
    engine_url = f"postgresql://{CITYDBV4_USER}:{CITYDBV4_PASSWORD}@{CITYDBV4_HOST}:{CITYDBV4_PORT}/{CITYDBV4_DB}"
    engine = create_engine(engine_url)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    inspector = inspect(engine)
    tables = inspector.get_table_names(schema=SCHEMA)

    for table in tables:
        with engine.connect() as conn:
            columns_query = text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = :schema AND table_name = :table
            """)
            result = conn.execute(columns_query, {"schema": SCHEMA, "table": table})
            columns = [row[0] for row in result]

        # fetch columns related geometry data properly
        select_parts = []
        for col in columns:
            if col.lower() in ("geom", "the_geom", "geometry"):
                select_parts.append(f'ST_AsText("{col}") AS "{col}"')
            else:
                select_parts.append(f'"{col}"')

        select_sql = f'SELECT {", ".join(select_parts)} FROM "{SCHEMA}"."{table}"'
        df = pd.read_sql_query(select_sql, con=engine)

        output_file = os.path.join(OUTPUT_DIR, f"{table}.csv")
        df.to_csv(output_file, index=False)
        print(f"Exported {output_file}")
