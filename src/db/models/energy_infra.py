from src.services.loader import utils


def create_common_data_table(schema: str):
    # Create parent table with all the columns that will be used by childern tables
    sql = f"""
            DROP SCHEMA IF EXISTS {schema} CASCADE;
            CREATE SCHEMA IF NOT EXISTS {schema};

            CREATE TABLE {schema}.common_data (
                index SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                commissioning_date DATE,
                decommissioning_date DATE,
                location DOUBLE PRECISION[][],
                manufacturer TEXT
                OEO_id INTEGER
            );
    """

    utils.sql_query(sql)


def import_models():
    schema = "energy_infra"
    create_common_data_table(schema)
