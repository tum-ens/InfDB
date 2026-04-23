"""
Main entry point for the buildings-to-street tool.
Handles InfDB initialization, database connection, logging, and demo execution.
"""

# Import packages
import os

from infdb import InfDB

from src import buildings_to_street


def main():
    """
    Initializes InfDB handler, sets up logging, connects to the database,
    and runs the demo function. Handles exceptions and logs errors.
    """

    # Initialize InfDB handler
    infdb = InfDB(tool_name="buildings-to-street", config_path="configs")
    log = infdb.get_logger()
    ags = infdb.get_env_variable("AGS")

    # Start message
    log.info(f"Starting {infdb.get_toolname()} tool")
    log.info("AGS environment variable: %s", ags)

    try:
        # ===========================================================
        # Start your added python code in folder "src"
        # ===========================================================
        log.info("Running python code ...")
        buildings_to_street.example_function(variable="Hello, InfDB!")

        # ===========================================================
        # Start your added sql scripts in folder "sql"
        # ===========================================================
        log.info("Running SQL scripts ...")

        streets_id = infdb.get_config_value([infdb.get_toolname(), "data", "streets", "id-column"])
        buildings_id = infdb.get_config_value([infdb.get_toolname(), "data", "buildings", "id-column"])

        # Define ID expressions: Use column if exists, else generate stable hash from geometry
        if streets_id == "None" or streets_id is None:
            streets_geom = infdb.get_config_value([infdb.get_toolname(), "data", "streets", "geom-column"])
            streets_id_expr = f"md5(ST_AsBinary(s.{streets_geom}))"
        else:
            streets_id_expr = f"s.{streets_id}::text"

        if buildings_id == "None" or buildings_id is None:
            buildings_geom = infdb.get_config_value([infdb.get_toolname(), "data", "buildings", "geom-column"])
            buildings_id_expr = f"md5(ST_AsBinary(b.{buildings_geom}))"
        else:
            buildings_id_expr = f"b.{buildings_id}::text"

        format_params = {
            "ags": ags,
            "streets_schema": infdb.get_config_value([infdb.get_toolname(), "data", "streets", "schema"]),
            "streets_table": infdb.get_config_value([infdb.get_toolname(), "data", "streets", "table"]),
            "streets_id_expr": streets_id_expr,
            "streets_geom": infdb.get_config_value([infdb.get_toolname(), "data", "streets", "geom-column"]),
            "buildings_schema": infdb.get_config_value([infdb.get_toolname(), "data", "buildings", "schema"]),
            "buildings_table": infdb.get_config_value([infdb.get_toolname(), "data", "buildings", "table"]),
            "buildings_id_expr": buildings_id_expr,
            "buildings_geom": infdb.get_config_value([infdb.get_toolname(), "data", "buildings", "geom-column"]),
            "output_schema": infdb.get_config_value([infdb.get_toolname(), "data", "output", "schema"]),
            "output_table": infdb.get_config_value([infdb.get_toolname(), "data", "output", "table"]),
        }
        SQL_DIR = os.path.join("sql")  # add subfolders here if needed ("sql/subfolder")
        infdb.connect().execute_sql_files(SQL_DIR, format_params=format_params)
        infdb.stop_logger()

    except Exception as e:
        log.error(f"Something went wrong: {str(e)}")
        infdb.stop_logger()
        raise e


if __name__ == "__main__":
    main()
