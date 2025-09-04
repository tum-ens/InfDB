import logging
import psycopg2
import time
import os


log = logging.getLogger(__name__)


class PostgreSQLExecutor:
    def __init__(self, host, port, database, username, password, input_schema=None, output_schema=None):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.connection = None
        self.cursor = None

        # Schema configuration
        # self.input_schema = SCHEMA_CONFIG['input_schema']
        # self.output_schema = SCHEMA_CONFIG['output_schema']
    
    def get_schema_params(self):
        """Get schema parameters for SQL template substitution"""
        return {
            'input_schema': self.input_schema,
            'output_schema': self.output_schema
        }

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
            )
            self.cursor = self.connection.cursor()
            log.info(
                f"Successfully connected to PostgreSQL database at {self.host}:{self.port}"
            )

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
            with open(full_path, "r", encoding="utf-8") as file:
                sql_content = file.read()

            # Apply schema parameter substitution
            # schema_params = self.get_schema_params()
            # sql_content = sql_content.format(**schema_params)

            log.info(f"Executing {os.path.join(sql_dir, file_path)}")
            self.cursor.execute(sql_content)
            self.connection.commit()
            log.info(
                f"Successfully executed {file_path} in {round(time.time() - start_time, 2)} seconds"
            )

        except Exception as e:
            log.error(
                f"Error executing {file_path} after {round(time.time() - start_time, 2)} seconds"
            )
            self.connection.rollback()
            raise e

    def execute_sql_scripts(self, sql_dir, script_files):
        """Execute multiple SQL script files in order"""
        try:
            self.connect()

            if isinstance(script_files, str):
                script_files = [script_files]
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