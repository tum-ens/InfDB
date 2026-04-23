import os
import sys
from typing import Dict

from infdb import InfDB

from . import utils


def load(infdb: InfDB) -> None:
    """Dumps schema from a source DB and restores it into the target Postgres.

    Behavior preserved:
    - Early exit (True) when feature flag `need` is inactive.
    - Skip dump step if the dump file already exists.
    - Use pg_dump for export and pg_restore for import with the original flags.
    """
    log = infdb.get_worker_logger()
    try:
        if not utils.if_active("need", infdb):
            return True

        # Dump input schema from source database
        TOOL_NAME = infdb.get_toolname()
        source_host = infdb.get_config_value([TOOL_NAME, "sources", "need", "host"])
        source_port = infdb.get_config_value([TOOL_NAME, "sources", "need", "port"])
        source_db = infdb.get_config_value([TOOL_NAME, "sources", "need", "database"])
        source_user = infdb.get_config_value([TOOL_NAME, "sources", "need", "user"])
        source_password = infdb.get_config_value([TOOL_NAME, "sources", "need", "password"])
        schema_input = infdb.get_config_value([TOOL_NAME, "sources", "need", "schema_input"])

        # Create dump file path
        path_dump = infdb.get_config_path([TOOL_NAME, "sources", "need", "path_dump"], type="loader")
        file_dump = os.path.join(path_dump, "need.dump")
        os.makedirs(os.path.dirname(file_dump), exist_ok=True)

        # Dump schema from source database (skip if already present)
        if os.path.exists(file_dump):
            log.info("Dump file %s already exists and will be skipped", file_dump)
        else:
            log.info(
                "Dumping need data from source database %s schema %s to %s...",
                source_db,
                schema_input,
                file_dump,
            )
            dump_cmd = (
                f"PGPASSWORD={source_password} "
                f"pg_dump -h {source_host} -p {source_port} -U {source_user} "
                f"-d {source_db} -n {schema_input} -F c -f {file_dump}"
            )
            utils.do_cmd(dump_cmd)

        # Restore dump into target database
        log.info("Restoring need data from dump file %s into target database...", file_dump)
        params: Dict[str, str] = infdb.get_db_parameters_dict()
        restore_cmd = (
            f"PGPASSWORD={params['password']} "
            f"pg_restore -h {params['host']} -p {params['exposed_port']} -U {params['user']} "
            f"-d {params['db']} -j 4 --clean --if-exists --no-owner --role={params['user']} {file_dump}"
        )
        utils.do_cmd(restore_cmd)

        log.info("Need data loaded successfully")
        sys.exit(0)

    except Exception as err:
        log.exception("An error occurred while processing NEED data: %s", str(err))
        sys.exit(1)
