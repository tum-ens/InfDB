"""
Main entry point for the infdb-basedata-ways tool.
Handles InfDB initialization, database connection, logging, and demo execution.
"""

# Import packages
import os

from infdb import InfDB

def _sql_quote(s: str) -> str:
    # SQL single-quote escaping
    return "'" + str(s).replace("'", "''") + "'"


def _sql_in_tuple(values) -> str:
    """
    Returns a SQL tuple like ('a','b','c').
    If empty -> (NULL) (but we also pass an enabled flag to avoid using it)
    """
    values = list(values or [])
    if not values:
        return "(NULL)"
    return "(" + ",".join(_sql_quote(v) for v in values) + ")"


def _build_objektart_conditions(klasse_objektart_filter: dict) -> str:
    """
    Build SQL OR conditions:
      (klasse='Bundesstraße' AND objektart IN ('Strassenachse','Fahrbahnachse'))
      OR (klasse='Bundesautobahn' AND objektart IN ('Strassenachse'))
    If empty -> FALSE
    """
    if not klasse_objektart_filter:
        return "FALSE"

    parts = []
    for klasse, allowed_objektarten in klasse_objektart_filter.items():
        in_list = _sql_in_tuple(allowed_objektarten)
        parts.append(f"(klasse={_sql_quote(klasse)} AND objektart IN {in_list})")
    return " OR ".join(parts)

def main():
    """
    Initializes InfDB handler, sets up logging, connects to the database,
    and runs the demo function. Handles exceptions and logs errors.
    """

    # Initialize InfDB handler
    infdb = InfDB(tool_name="infdb-basedata-ways", config_path="configs/config-infdb-basedata-ways.yml")

    # Start message
    log = infdb.get_logger()
    log.info(f"Starting {infdb.get_toolname()} tool")

    ags = infdb.get_env_variable("AGS")
    log.info("AGS environment variable: %s", ags)

    try:
        
        tool = infdb.get_toolname()
        # ===========================================================
        # Start your added sql scripts in folder "sql"
        # ===========================================================
        log.info("Running SQL scripts ...")

        input_schema = infdb.get_config_value([tool, "data", "input_schema"])
        output_schema = infdb.get_config_value([tool, "data", "output_schema"])
        epsg = infdb.get_config_value([tool, "hosts", "postgres", "epsg"])
        if epsg is None:
        # fallback: many German datasets use EPSG:25832 (ETRS89 / UTM zone 32N)
            epsg = 3035

        klasse_filter = infdb.get_config_value([tool, "data", "klasse_filter"]) or []
        klasse_objektart_filter = infdb.get_config_value([tool, "data", "klasse_objektart_filter"]) or {}

        klasse_filter_enabled = bool(klasse_filter)
        objektart_filter_enabled = bool(klasse_objektart_filter)

        classes_with_obj_filter = list(klasse_objektart_filter.keys())

        format_params = {
            "ags": ags,
            "input_schema": input_schema,
            "output_schema": output_schema,
            "use_address_information": str(
               infdb.get_config_value([tool, "data", "use_address_information"])
            ).lower(),
            "apply_length_filter": str(
               infdb.get_config_value([tool, "data", "apply_length_filter"])
            ).lower(),
            "apply_loop_filter": str(
               infdb.get_config_value([tool, "data", "apply_loop_filter"])
            ).lower(),
            "apply_isolated_filter": str(
               infdb.get_config_value([tool, "data", "apply_isolated_filter"])
            ).lower(),
            "min_length_meter": infdb.get_config_value([tool, "data", "min_length_meter"]),
            "epsg": epsg,

            # NEW: Step 1 filter params
            "klasse_filter_enabled": str(klasse_filter_enabled).lower(),  # 'true' / 'false'
            "klasse_filter_tuple": _sql_in_tuple(klasse_filter),

            "objektart_filter_enabled": str(objektart_filter_enabled).lower(),  # 'true' / 'false'
            "classes_with_obj_filter_tuple": _sql_in_tuple(classes_with_obj_filter),
            "objektart_filter_conditions": _build_objektart_conditions(klasse_objektart_filter),
            "tool_name": infdb.get_toolname(),
            "process_id": os.getpid(),           
        }

        log.info("Running SQL scripts ...")
        SQL_DIR = os.path.join("sql")
        infdb.connect().execute_sql_files(SQL_DIR, format_params=format_params)

        # ===========================================================
        # Demonstrate database querying - remove or comment out if not needed
        # ===========================================================
        
        infdb.stop_logger()

    except Exception as e:
        log.error(f"Something went wrong: {str(e)}")
        infdb.stop_logger()
        raise e


if __name__ == "__main__":
    main()
