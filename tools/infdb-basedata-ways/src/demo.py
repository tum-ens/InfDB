"""
Demo module for database operations with InfDB.

This module provides example functions for connecting to and querying
the InfDB database using both the InfDB client and direct SQLAlchemy connections.
"""

import os

import geopandas as gpd
from sqlalchemy import create_engine


def sql_demo(infdb):
    """
    Demonstrate SQL script execution using InfDB.

    Drops and recreates the output schema, then executes all SQL scripts
    from the sql/ directory in alphabetical order. Format parameters are
    passed to allow dynamic schema names in SQL templates.

    Args:
        infdb: InfDB client instance with database connection.

    Note:
        - SQL files can use placeholders like {output_schema}, {input_schema}
        - Scripts are executed in alphabetical order (use prefixes: 01_, 02_)
    """
    # Schema configuration
    format_params = {
        "input_schema": infdb.get_config_value([infdb.get_toolname(), "data", "input_schema"]),
        "output_schema": infdb.get_config_value([infdb.get_toolname(), "data", "output_schema"]),
    }

    # Drop output schema if exists for development purposes
    infdb.connect().execute_query("DROP SCHEMA IF EXISTS {output_schema} CASCADE".format(**format_params))

    # Execute sql scripts
    infdb.get_logger().info("Running SQL scripts ...")
    SQL_DIR = os.path.join("sql")  # add subfolders here if needed
    infdb.connect().execute_sql_files(SQL_DIR, format_params=format_params)


def database_demo(infdb):
    """
    Demonstrate database querying using InfDB client.

    Retrieves building heat demand data from the kwp schema using
    the InfDB database engine and loads it into a GeoDataFrame.

    Args:
        infdb: InfDB client instance with database connection.

    Returns:
        GeoDataFrame: Buildings with heat demand data and geometry.
    """
    engine = infdb.get_db_engine()
    sql = "SELECT * FROM opendata.buildings_lod2"
    gdf_buildings = gpd.read_postgis(sql, engine)
    gdf_buildings.head()

    return gdf_buildings


def database_demo_sqlalchemy(infdb):
    """
    Demonstrate direct SQLAlchemy database connection without using InfDB client
    (not recommended - configs from infDB are not considered automatically).

    Creates a direct database connection using SQLAlchemy engine
    and queries building heat demand data from the kwp schema.
    Uses hardcoded connection parameters suitable for Docker environments.

    Returns:
        GeoDataFrame: Buildings with heat demand data and geometry.
    """
    # Database connection parameters
    user = "infdb_user"
    password = "infdb"
    host = "ds1.need.energy"
    port = "54328"
    db = "infdb"

    # or get parameters from infDB config
    infdb.get_db_parameters_dict()
    user = infdb.get_db_parameters_dict().get("user")
    password = infdb.get_db_parameters_dict().get("password")
    host = infdb.get_db_parameters_dict().get("host")
    port = infdb.get_db_parameters_dict().get("port")
    db = infdb.get_db_parameters_dict().get("database")

    db_connection_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"

    engine = create_engine(db_connection_url)
    sql = "SELECT * FROM opendata.buildings_lod2"
    gdf_buildings = gpd.read_postgis(sql, engine)
    gdf_buildings.head()

    return gdf_buildings


def get_env_variables(infdb):
    """
    Retrieve environment variables for the InfDB tool.

    Args:
        infdb: InfDB client instance with database connection.

    Returns:
        dict: Environment variables for the InfDB tool.
    """
    return infdb.get_env_variables_dict()
