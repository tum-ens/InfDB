# common_data.py

from tools.loader.src import utils

def create_common_data_table(schema: str):
    sql = f"""
        DROP SCHEMA IF EXISTS {schema} CASCADE;
        CREATE SCHEMA IF NOT EXISTS {schema};

        CREATE TABLE {schema}.common_data (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            commissioning_date DATE,
            decommissioning_date DATE,
            location DOUBLE PRECISION[][],
            manufacturer TEXT,
            OEO_id INTEGER
        );
    """
    utils.sql_query(sql)
