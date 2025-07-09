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
                manufacturer TEXT,
                OEO_id INTEGER
            );
    """

    utils.sql_query(sql)


def create_transformer_table(schema):
    sql = f"""
    CREATE TABLE {schema}.heat_pump (
	heating_capacity_kw FLOAT,
    cop_heating FLOAT,
    source_type TEXT
) INHERITS ({schema}.common_data);
    """
    utils.sql_query(sql)


def create_line_table(schema):
    sql = f"""
        CREATE TABLE {schema}.line (
            from_bus INTEGER,
            to_bus INTEGER,
            length_km DOUBLE PRECISION,
            geodata DOUBLE PRECISION[][],
            std_type TEXT
        ) INHERITS ({schema}.common_data);
    """
    utils.sql_query(sql)


def create_switch_table(schema):
    sql = f"""
        CREATE TABLE {schema}.switch (
            bus INTEGER,
            element INTEGER,
            et TEXT,
            closed BOOLEAN,
            type INTEGER,
            name TEXT,
            z_ohm DOUBLE PRECISION,
            in_ka DOUBLE PRECISION
        ) INHERITS ({schema}.common_data);
    """
    utils.sql_query(sql)


def create_bus_table(schema):
    sql = f"""
        CREATE TABLE {schema}.bus (
            vn_kv INTEGER,
            geodata DOUBLE PRECISION[2],
            type TEXT,
            zone TEXT
        ) INHERITS ({schema}.common_data);
    """
    utils.sql_query(sql)


def electricity_network_components(schema):
    create_transformer_table(schema)
    create_line_table(schema)
    create_switch_table(schema)
    create_bus_table(schema)


def import_models():
    schema = "energy_infra"
    create_common_data_table(schema)
    electricity_network_components(schema)
