import os
import time
from typing import Any, Dict

from pyinfdb import InfDB


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

    # Mixed-use parameters consumed by 06_z_fill_mixed_use.sql
    mixed_use = infdb.get_config_value([infdb.get_toolname(), "mixed_use"])
    mu_weights = mixed_use["weights"]
    mu_share = mixed_use["share"]

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
        "mu_status": mixed_use["status"],
        "mu_min_floors": mixed_use["min_floors"],
        "mu_min_overlap": mixed_use["min_overlap"],
        "mu_threshold": mixed_use["threshold"],
        "mu_rescue_threshold": mixed_use["rescue_threshold"],
        "mu_rescue_max_per_cell": mixed_use["rescue_max_per_cell"],
        "mu_w_osm_residential": mu_weights["osm_residential"],
        "mu_w_mixed_area": mu_weights["mixed_area"],
        "mu_w_address": mu_weights["address"],
        "mu_w_residential_area": mu_weights["residential_area"],
        "mu_w_floors_3plus": mu_weights["floors_3plus"],
        "mu_w_industrial_area": mu_weights["industrial_area"],
        "mu_pedestrian_buffer_m": mu_share["pedestrian_buffer_m"],
        "mu_commercial_floors_pedestrian": mu_share["commercial_floors_pedestrian"],
        "mu_commercial_floors_default": mu_share["commercial_floors_default"],
        "mu_min_residential_share": mu_share["min_residential_share"],
        "mu_max_residential_share": mu_share["max_residential_share"],
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
        # TEMPORARY: skip 16_logging_and_constraints_for_lizmap.sql 
        sql_files = [
            f for f in sorted(os.listdir(BUILDINGS_SQL_DIR))
            if f.endswith(".sql") and not f.startswith("16_")
        ]
        db.execute_sql_files(BUILDINGS_SQL_DIR, file_list=sql_files, format_params=format_params)
        end_time = time.time()
        log.info("BUILDINGS SQL scripts completed in %.2f seconds", end_time - start_time)


    log.info("Successfully finished %s tool", infdb.get_toolname())
    infdb.stop_logger()


if __name__ == "__main__":
    main()
