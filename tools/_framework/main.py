"""
Main entry point for the choose-a-name tool.
Handles InfDB initialization, database connection, logging, and demo execution.
"""

# Import packages
import os

from infdb import InfDB

from src import choose_a_name, demo


def main():
    """
    Initializes InfDB handler, sets up logging, connects to the database,
    and runs the demo function. Handles exceptions and logs errors.
    """

    # Initialize InfDB handler
    infdb = InfDB(tool_name="choose-a-name", config_path="../configs/config-choose-a-name.yml")
    ags = infdb.get_env_variable("AGS")

    # Start message
    log = infdb.get_logger()
    log.info(f"Starting {infdb.get_toolname()} tool")
    log.info("AGS environment variable: %s", ags)

    try:
        # ===========================================================
        # Start your added python code in folder "src"
        # ===========================================================
        log.info("Running python code ...")
        choose_a_name.example_function(variable="Hello, InfDB!")

        # ===========================================================
        # Start your added sql scripts in folder "sql"
        # ===========================================================
        log.info("Running SQL scripts ...")
        format_params = {
            "input_schema": infdb.get_config_value([infdb.get_toolname(), "data", "input_schema"]),
            "output_schema": infdb.get_config_value([infdb.get_toolname(), "data", "output_schema"]),
        }
        SQL_DIR = os.path.join("sql")  # add subfolders here if needed ("sql/subfolder")
        infdb.connect().execute_sql_files(SQL_DIR, format_params=format_params)

        # ===========================================================
        # Demonstrate database querying - remove or comment out if not needed
        # ===========================================================
        log.info("Running demo ...")
        demo.sql_demo(infdb)
        demo.database_demo(infdb)
        demo.database_demo_sqlalchemy()
        infdb.stop_logger()

    except Exception as e:
        log.error(f"Something went wrong: {str(e)}")
        infdb.stop_logger()
        raise e


if __name__ == "__main__":
    main()
