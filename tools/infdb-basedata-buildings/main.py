import os
import time
from typing import Any, Dict

from infdb import InfDB


def main() -> None:
    """Run base-data SQL pipelines (WAYS, BUILDINGS, CONNECTIONS) against Postgres.

    Loads configuration and logging via `InfDB`, prepares format parameters, drops
    the output schema (if present), and executes the SQL directories in sequence.
    """
    # Load InfDB facade (config + logging)
    infdb = InfDB(tool_name="infdb-basedata-buildings", config_path="configs/config-infdb-basedata-buildings.yml")

    # Logger
    log = infdb.get_logger()
    ags = infdb.get_env_variable("AGS")
    log.info("Starting %s tool", infdb.get_toolname())
    log.info("AGS environment variable: %s", ags)

    # Config
    input_schema = infdb.get_config_value([infdb.get_toolname(), "data", "input_schema"])
    output_schema = infdb.get_config_value([infdb.get_toolname(), "data", "output_schema"])
    census_building_type_resolution = infdb.get_config_value(
        [infdb.get_toolname(), "data", "census_building_type_resolution"]
    )
    random_seed = infdb.get_config_value([infdb.get_toolname(), "data", "random_seed"])
    epsg = infdb.get_db_parameters_dict().get("epsg")

    format_params: Dict[str, Any] = {
        "ags": ags,
        "input_schema": input_schema,
        "output_schema": output_schema,
        "list_gemeindeschluessel": ags,
        "EPSG": epsg,
        "census_building_type_resolution": census_building_type_resolution,
        "random_seed": random_seed,
        "tool_name": infdb.get_toolname(),
        "process_id": os.getpid(),
    }

    log.info("Input schema: %s", input_schema)
    log.info("Output schema: %s", output_schema)
    BUILDINGS_SQL_DIR: str = os.path.join("sql", "buildings_sql")
    # Database work (context-managed)
    with infdb.connect() as db:

        # Execute BUILDINGS scripts
        # if you wish to fully reset buildings table, use the following line:
        # DELETE FROM public.databasechangelog WHERE labels like '%buildings%';
        start_time = time.time()
        log.info("Running BUILDINGS SQL scripts")
        db.execute_sql_files(BUILDINGS_SQL_DIR, format_params=format_params)
        end_time = time.time()
        log.info("BUILDINGS SQL scripts completed in %.2f seconds", end_time - start_time)


    log.info("Successfully finished %s tool", infdb.get_toolname())
    infdb.stop_logger()


if __name__ == "__main__":
    main()
