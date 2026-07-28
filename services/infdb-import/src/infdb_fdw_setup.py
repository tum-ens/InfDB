"""
Foreign Data Wrapper (FDW) setup module for InfDB.

This module sets up PostgreSQL Foreign Data Wrapper to access the central
opendata schema from a remote InfDB instance without duplicating data.
"""

from pyinfdb import InfDB


def is_active(infdb: InfDB):
    """Returns whether this tool is active based on the config."""
    fdw_config = infdb.get_config_value([infdb.get_toolname(), "fdw"])
    isActive : str = fdw_config["status"]
    return isActive.lower() == "active"

def setup_fdw(infdb: InfDB) -> None:
    """
    Sets up Foreign Data Wrapper to access the central opendata schema.

    This function:
    1. Enables the postgres_fdw extension
    2. Creates a foreign server pointing to the central InfDB instance
    3. Creates a foreign schema mapping to access the opendata schema
    4. Grants necessary permissions

    Args:
        infdb: InfDB handler instance
    """
    log = infdb.get_logger()

    # Get FDW configuration
    fdw_config = infdb.get_config_value([infdb.get_toolname(), "fdw"])
    central_host = fdw_config["central_db"]["host"]
    central_port = fdw_config["central_db"]["port"]
    central_db = fdw_config["central_db"]["db"]
    central_user = fdw_config["central_db"]["user"]
    central_password = fdw_config["central_db"]["password"]
    foreign_schema = fdw_config["foreign_schema"]
    local_schema = fdw_config["local_schema"]
    read_only = fdw_config.get("read_only", True)

    log.info(f"Setting up FDW to access '{foreign_schema}' schema from central InfDB instance")
    log.info(f"Central DB: {central_host}:{central_port}/{central_db}")
    log.info(f"FDW read-only mode: {read_only}")

    # Connect to local database
    with infdb.connect() as db:
        try:
            # 1. Enable postgres_fdw extension
            log.info("Enabling postgres_fdw extension...")
            db.execute_query("CREATE EXTENSION IF NOT EXISTS postgres_fdw;")

            # 2. Create foreign server
            server_name = "infdb_central_server"
            log.info(f"Creating foreign server '{server_name}'...")
            create_server_sql = f"""
                CREATE SERVER IF NOT EXISTS {server_name}
                FOREIGN DATA WRAPPER postgres_fdw
                OPTIONS (
                    host '{central_host}',
                    port '{central_port}',
                    dbname '{central_db}'
                );
            """
            db.execute_query(create_server_sql)

            # 3. Create user mapping
            log.info("Creating user mapping for foreign server...")
            create_mapping_sql = f"""
                CREATE USER MAPPING IF NOT EXISTS FOR CURRENT_USER
                SERVER {server_name}
                OPTIONS (
                    user '{central_user}',
                    password '{central_password}'
                );
            """
            db.execute_query(create_mapping_sql)

            # 4. Drop and recreate foreign schema (ensures clean import)
            log.info(f"Preparing foreign schema '{local_schema}' mapping to remote '{foreign_schema}'...")
            # Drop existing schema to ensure clean import (idempotent)
            db.execute_query(f"DROP SCHEMA IF EXISTS {local_schema} CASCADE;")
            # Create fresh schema
            db.execute_query(f"CREATE SCHEMA {local_schema};")

            # 5. Import foreign schema
            log.info(f"Importing foreign schema '{foreign_schema}' into local schema '{local_schema}'...")
            import_schema_sql = f"""
                IMPORT FOREIGN SCHEMA {foreign_schema}
                FROM SERVER {server_name}
                INTO {local_schema};
            """
            db.execute_query(import_schema_sql)

            # 6. Grant permissions (optional - adjust as needed)
            log.info("Granting permissions on foreign schema...")
            if read_only:
                grant_sql = f"""
                    GRANT USAGE ON SCHEMA {local_schema} TO PUBLIC;
                    GRANT SELECT ON ALL TABLES IN SCHEMA {local_schema} TO PUBLIC;
                    ALTER DEFAULT PRIVILEGES IN SCHEMA {local_schema}
                    GRANT SELECT ON TABLES TO PUBLIC;
                """
            else:
                grant_sql = f"""
                    GRANT USAGE ON SCHEMA {local_schema} TO PUBLIC;
                    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {local_schema} TO PUBLIC;
                    ALTER DEFAULT PRIVILEGES IN SCHEMA {local_schema}
                    GRANT ALL PRIVILEGES ON TABLES TO PUBLIC;
                """
            db.execute_query(grant_sql)

            log.info("FDW setup completed successfully!")
            log.info(f"You can now access the central opendata schema via: {local_schema}.table_name")
            log.info("Example: SELECT * FROM opendata_fdw.buildings;")

        except Exception as e:
            log.error(f"FDW setup failed: {str(e)}")
            # Clean up on failure
            try:
                db.execute_query(f"DROP SCHEMA IF EXISTS {local_schema} CASCADE;")
                db.execute_query(f"DROP USER MAPPING IF EXISTS FOR CURRENT_USER SERVER {server_name};")
                db.execute_query(f"DROP SERVER IF EXISTS {server_name};")
                log.info("Cleaned up failed FDW setup")
            except Exception as cleanup_error:
                log.error(f"Cleanup failed: {str(cleanup_error)}")
            raise e
