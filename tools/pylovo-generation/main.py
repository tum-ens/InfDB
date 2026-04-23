#!/usr/bin/env python3
"""
Pylovo Generation Tool - Interactive AGS Selection
Generates synthetic low-voltage grid topologies for German municipalities.
"""

import os
import subprocess
import sys
from typing import List

from infdb import InfDB


def query_database(infdb: InfDB, query: str) -> str:
    """Execute a PostgreSQL query and return the result."""
    db_params = infdb.get_db_parameters_dict()
    conn_string = (
        f"postgresql://{db_params['user']}:{db_params['password']}"
        f"@{db_params['host']}:{db_params['exposed_port']}/{db_params['db']}"
    )
    try:
        result = subprocess.run(["psql", conn_string, "-t", "-c", query], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def get_available_ags(infdb: InfDB) -> List[str]:
    """Query database for available AGS codes from opendata.scope table."""
    log = infdb.get_logger()
    log.info("Fetching available AGS codes from opendata.scope table...")
    ags_query = 'SELECT "AGS" FROM opendata.scope WHERE "AGS" IS NOT NULL ORDER BY "AGS"'
    result = query_database(infdb, ags_query)
    # Parse result and remove leading zeros
    ags_list = [line.strip().lstrip("0") for line in result.split("\n") if line.strip()]
    return ags_list


def prompt_user_selection(infdb: InfDB, available_ags: List[str]) -> str:
    """Display available AGS codes and prompt user for selection."""
    log = infdb.get_logger()
    # Blue color for the ags prompt
    BLUE = "\033[94m"
    RESET = "\033[0m"

    log.info(
        "Enter AGS codes to generate low voltage grids: Single AGS ➜ 9185149 | "
        "Multiple AGS ➜ 9185149,9185150 | All AGS ➜ all"
    )
    log.info(f"{BLUE}Available municipalities (AGS codes):{RESET}")
    for ags in available_ags:
        log.info(f"{BLUE}{ags}{RESET}")

    selection = input(f"{BLUE}➜ Your selection: {RESET}").strip()

    if not selection:
        log.error("No AGS codes entered")
        sys.exit(1)

    if selection.lower() == "all":
        ags_list = ",".join(available_ags)
        log.info("Selected: All municipalities (%s)", ags_list)
    else:
        # Remove leading zeros from user input (in case they copy from database)
        ags_list = ",".join([ags.strip().lstrip("0") for ags in selection.split(",")])
        log.info("Selected: %s", ags_list)

    return ags_list


def run_pylovo_setup(infdb: InfDB) -> None:
    """Run pylovo-setup to initialize the database schema."""
    log = infdb.get_logger()
    log.info("Setting up pylovo database...")
    os.chdir("/app/src/pylovo")
    result = subprocess.run(["uv", "run", "--active", "pylovo-setup"], check=False)
    if result.returncode != 0:
        log.error("pylovo-setup failed")
        sys.exit(1)


def run_pylovo_generate(infdb: InfDB, ags_list: str) -> None:
    """Run pylovo-generate for the selected AGS codes."""
    log = infdb.get_logger()
    log.info(f"Generating synthetic grids for AGS: {ags_list}")
    result = subprocess.run(["uv", "run", "--active", "pylovo-generate", "--ags", ags_list], check=False)
    if result.returncode == 0:
        log.info("Grid generation completed successfully")
    else:
        log.error("Grid generation failed")
    sys.exit(result.returncode)


def main() -> None:
    """Main entry point for pylovo-generation tool."""
    # Load InfDB facade (config + logging)
    infdb = InfDB(tool_name="pylovo-generation", config_path="configs/conf-pylovo-generation.yml")
    # Logger
    log = infdb.get_logger()
    log.info("Starting %s tool", infdb.get_toolname())
    # Get schemas from config
    input_schema = infdb.get_config_value([infdb.get_toolname(), "data", "input_schema"])
    output_schema = infdb.get_config_value([infdb.get_toolname(), "data", "output_schema"])
    log.info("Configuration:")
    log.info("  Input schema: %s", input_schema)
    log.info("  Output schema: %s", output_schema)
    # Set environment variables for pylovo (it doesn't use InfDB directly)
    os.environ["TARGET_SCHEMA"] = output_schema
    os.environ["INFDB_SOURCE_SCHEMA"] = input_schema

    # Check AGS selection: config file or interactive
    config_ags = infdb.get_config_value([infdb.get_toolname(), "data", "ags_list"])

    if config_ags and config_ags != "None":
        # Use AGS from config file
        log.info("Using AGS from config file: %s", config_ags)
        ags_selection = config_ags
    else:
        # Interactive mode: query database and prompt user
        available_ags = get_available_ags(infdb)
        ags_selection = prompt_user_selection(infdb, available_ags)

    # Run pylovo
    run_pylovo_setup(infdb)
    run_pylovo_generate(infdb, ags_selection)
    log.info("Successfully finished %s tool", infdb.get_toolname())
    infdb.stop_logger()


if __name__ == "__main__":
    main()
