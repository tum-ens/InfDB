#!/usr/bin/env python3
"""
Pylovo Generation Tool
Generates synthetic low-voltage grid topologies for German municipalities.
AGS selection is handled externally via the AGS environment variable (set by tools.sh / run_ags.py)
or via the config file (configs/config-pylovo-generation.yml).
"""

import os
import subprocess
import sys

from pyinfdb import InfDB


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
    infdb = InfDB(tool_name="pylovo-generation", config_path="configs/config-pylovo-generation.yml")
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

    # Check AGS selection: env var -> config file
    env_ags = os.environ.get("AGS")
    config_ags = infdb.get_config_value([infdb.get_toolname(), "data", "ags_list"])

    if env_ags:
        # Use AGS from environment variable (set by tools.sh / run_ags.py)
        log.info("Using AGS from environment variable: %s", env_ags)
        ags_selection = env_ags
    elif config_ags and config_ags != "None":
        # Use AGS from config file
        log.info("Using AGS from config file: %s", config_ags)
        ags_selection = config_ags
    else:
        log.error("No AGS defined. Set the AGS environment variable or configure 'data.ags_list' in the config file.")
        sys.exit(1)

    # Run pylovo
    run_pylovo_setup(infdb)
    run_pylovo_generate(infdb, ags_selection)
    log.info("Successfully finished %s tool", infdb.get_toolname())
    infdb.stop_logger()


if __name__ == "__main__":
    main()
