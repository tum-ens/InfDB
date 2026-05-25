"""
Main entry point for the infdb-fdw-setup tool.
Sets up Foreign Data Wrapper (FDW) to access the central opendata schema.
"""

# Import packages
import os

from infdb import InfDB

from src import infdb_fdw_setup


def main():
    """
    Initializes InfDB handler, sets up logging, connects to the database,
    and runs the FDW setup function. Handles exceptions and logs errors.
    """

    # Initialize InfDB handler
    infdb = InfDB(tool_name="infdb-fdw-setup", config_path="configs/config-infdb-fdw-setup.yml")

    # only run if config-infdb-fdw-setup.yml status is active
    if not infdb_fdw_setup.is_active(infdb):
        print(f"{infdb.get_toolname()} tool is not active. Please check the configuration.")
        return
    
    # Start message
    log = infdb.get_logger()
    log.info(f"Starting {infdb.get_toolname()} tool")

    try:
        # Run FDW setup
        log.info("Setting up Foreign Data Wrapper for opendata schema...")
        infdb_fdw_setup.setup_fdw(infdb)

        infdb.stop_logger()

    except Exception as e:
        log.error(f"Something went wrong: {str(e)}")
        infdb.stop_logger()
        raise e


if __name__ == "__main__":
    main()
