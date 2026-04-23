"""
Main entry point for the infdb-metadata tool.
Handles InfDB initialization, database connection, logging, and demo execution.
"""

# Import packages
import src.infdb_metadata as infdb_metadata
from infdb import InfDB


def main():
    """
    Initializes InfDB handler, sets up logging, connects to the database,
    and runs the demo function. Handles exceptions and logs errors.
    """

    # Initialize InfDB handler
    infdb = InfDB(tool_name="infdb-metadata")
    log = infdb.get_logger()
    # Start messagero
    log.info(f"Starting {infdb.get_toolname()} tool")

    try:
        # ===========================================================
        # Start your added python code in folder "src"
        # ===========================================================
        log.info("Running python code ...")
        client = infdb.connect()
        infdb_metadata.run_with_infdb(client, infdb.logger)
        infdb.stop_logger()

    except Exception as e:
        log.error(f"Something went wrong: {str(e)}")
        infdb.stop_logger()

        raise e


if __name__ == "__main__":
    main()
