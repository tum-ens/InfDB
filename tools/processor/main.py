import psycopg2
import os
import logging
import time
from src import config, utils, logger

log = logging.getLogger(__name__)

# Initialize logging
listener = logger.setup_main_logger(None)

# SQL files directory and list of files to execute in order
WAYS_SQL_DIR = os.path.join(os.path.dirname(__file__), 'sql', 'ways_sql')
BUILDINGS_SQL_DIR = os.path.join(os.path.dirname(__file__), 'sql', 'buildings_sql')

WAYS_SQL_FILES = [
    '00_cleanup.sql',
    '01_create_functions.sql',
    '02_create_ways_table.sql',
    '03_fill_id_ways_table.sql',
    '04_create_names_table.sql',
    '05_assign_postcode_to_ways.sql',
]
BUILDINGS_SQL_FILES = [
    '00_cleanup.sql',
    '01_create_functions.sql',
    '02_create_buildings_table.sql',
    '03_fill_id_object_id_building_use.sql',
    '04_fill_height.sql',
    '05_fill_floor_area_geom.sql',
    '06_create_touching_buildings_temp_tables.sql',
    '07_fill_floor_number.sql',
    '08_prepare_grid.sql',
    '09_fill_occupants.sql',
    '10_fill_households.sql',
    '11_fill_construction_year.sql',
    '12_fill_building_type.sql',
    '13_assign_postcode_to_buildings.sql',
    '14_create_address_table.sql',
    '15_assign_streets_to_buildings.sql',
    '16_add_constraints.sql'
]


class PostgreSQLExecutor:
    def __init__(self, host, port, database, username, password):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.connection = None
        self.cursor = None

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password
            )
            self.cursor = self.connection.cursor()
            log.info(f"Successfully connected to PostgreSQL database at {self.host}:{self.port}")

        except Exception as e:
            log.error(f"Failed to connect to database: {str(e)}")
            raise

    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        log.info("Database connection closed")

    def execute_sql_file(self, sql_dir, file_path):
        """Execute SQL commands from a file"""
        start_time = time.time()
        try:
            full_path = os.path.join(sql_dir, file_path)
            with open(full_path, 'r', encoding='utf-8') as file:
                sql_content = file.read()

            log.info(f"Executing {os.path.join(sql_dir, file_path)}")
            self.cursor.execute(sql_content)
            self.connection.commit()
            log.info(f"✅ Successfully executed {file_path} in {round(time.time() - start_time, 2)} seconds")

        except Exception as e:
            log.error(f"💥 Error executing {file_path} after {round(time.time() - start_time, 2)} seconds")
            self.connection.rollback()
            raise e

    def execute_sql_scripts(self, sql_dir, script_files):
        """Execute multiple SQL script files in order"""
        try:
            self.connect()

            total_files = len(script_files)
            log.info(f"Starting execution of {total_files} SQL scripts")

            for i, script_file in enumerate(script_files, 1):
                if not os.path.exists(os.path.join(sql_dir, script_file)):
                    msg = f"SQL file not found: {script_file}"
                    log.error(msg)
                    raise FileNotFoundError(msg)

                log.info(f"[{i}/{total_files}] Executing script: {script_file}")
                self.execute_sql_file(sql_dir, script_file)

                # Small delay between scripts
                if i < total_files:
                    time.sleep(0.5)
        except Exception as e:
            raise e
        finally:
            self.disconnect()


def main():
    try:
        # Database configuration
        parameters = config.get_db_parameters("citydb")

        # Initialize database executor
        db_executor = PostgreSQLExecutor(
            host=parameters["host"],
            port=parameters["exposed_port"],
            database=parameters["db"],
            username=parameters["user"],
            password=parameters["password"]
        )

        # Validate all SQL files exist before starting
        missing_ways = [f for f in WAYS_SQL_FILES if not os.path.exists(os.path.join(WAYS_SQL_DIR, f))]
        missing_buildings = [f for f in BUILDINGS_SQL_FILES if not os.path.exists(os.path.join(BUILDINGS_SQL_DIR, f))]

        if missing_ways or missing_buildings:
            if missing_ways:
                log.error(f"Missing WAYS SQL files in {WAYS_SQL_DIR}/: {missing_ways}")
            if missing_buildings:
                log.error(f"Missing BUILDINGS SQL files in {BUILDINGS_SQL_DIR}/: {missing_buildings}")
            return 1


        # Execute WAYS scripts first
        log.info("Running WAYS SQL scripts")
        db_executor.execute_sql_scripts(WAYS_SQL_DIR, WAYS_SQL_FILES)

        # Then BUILDINGS scripts
        log.info("Running BUILDINGS SQL scripts")
        db_executor.execute_sql_scripts(BUILDINGS_SQL_DIR, BUILDINGS_SQL_FILES)

        log.info("🏠 Prepared buildings and ways successfully!")

    except Exception as e:
        log.error(f"💥 Something went wrong: {str(e)}")
        raise e


if __name__ == "__main__":
    main()