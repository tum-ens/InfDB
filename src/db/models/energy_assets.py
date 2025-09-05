# energy_assets.py

import utils

def create_heat_pump_table(schema):
    sql = f"""
        CREATE TABLE {schema}.heat_pump (
            generator TEXT,
            load TEXT,
            heating_capacity_kw FLOAT,
            cop_heating FLOAT,
            source_type TEXT
        ) INHERITS ({schema}.common_data);
    """
    utils.sql_query(sql)

def create_battery_storage_table(schema):
    sql = f"""
        CREATE TABLE {schema}.battery_storage (
            generator TEXT,
            load TEXT,
            capacity_kw FLOAT,
            max_charge FLOAT,
            max_discharge FLOAT
        ) INHERITS ({schema}.common_data);
    """
    utils.sql_query(sql)

def create_electric_vehicle_table(schema):
    sql = f"""
        CREATE TABLE {schema}.electric_vehicle (
            generator TEXT,
            load TEXT,
            battery_capacity_kw FLOAT,
            charge_rate_kw FLOAT
        ) INHERITS ({schema}.common_data);
    """
    utils.sql_query(sql)

def create_wind_turbine_table(schema):
    sql = f"""
        CREATE TABLE {schema}.wind_turbine (
            generator TEXT,
            load TEXT,
            rated_power_kw FLOAT,
            hub_height_m FLOAT,
            rotor_trip_efficiency FLOAT
        ) INHERITS ({schema}.common_data);
    """
    utils.sql_query(sql)

def create_photovoltaic_system_table(schema):
    sql = f"""
        CREATE TABLE {schema}.photovoltaic_system (
            generator TEXT,
            load TEXT,
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
    create_photovoltaic_system_table(schema)
