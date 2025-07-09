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


def create_heat_pump_table(schema):
    sql = f"""
        CREATE TABLE {schema}.heat_pump (
            heating_capacity_kw FLOAT,
            cop_heating FLOAT,
            source_type TEXT
        ) INHERITS ({schema}.common_data);
    """
    utils.sql_query(sql)


def create_battery_storage_table(schema):
    sql = f"""
        CREATE TABLE {schema}.battery_storage (
            capacity_kw FLOAT,
            max_charge FLOAT,
            max_discharge FLOAT
        ) INHERITS ({schema}.common_data);
    """
    utils.sql_query(sql)


def create_electric_vehicle_table(schema):
    sql = f"""
        CREATE TABLE {schema}.electric_vehicle (
            battery_capacity_kw FLOAT,
            charge_rate_kw FLOAT
        ) INHERITS ({schema}.common_data);
    """
    utils.sql_query(sql)


def create_wind_turbine_table(schema):
    sql = f"""
        CREATE TABLE {schema}.wind_turbine (
            rated_power_kw FLOAT,
            hub_height_m FLOAT,
            rotor_trip_efficiency FLOAT
        ) INHERITS ({schema}.common_data);
    """
    utils.sql_query(sql)
    

def create_photovolatic_system_table(schema):
    sql = f"""
        CREATE TABLE {schema}.photovolatic_system (
            rated_power_kw FLOAT,
            tilt FLOAT,
            area_m2 FLOAT
         ) INHERITS ({schema}.common_data);
    """
    utils.sql_query(sql)


def energy_assets(schema):
    create_heat_pump_table(schema)
    create_battery_storage_table(schema)
    create_electric_vehicle_table(schema)
    create_wind_turbine_table(schema)
    create_photovolatic_system_table(schema)


def import_models():
    schema = "energy_infra"
    create_common_data_table(schema)
    energy_assets(schema)
