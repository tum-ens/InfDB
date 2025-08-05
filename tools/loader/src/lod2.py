import os
import shutil
from . import config, utils, logger
import logging

log = logging.getLogger(__name__)

def load(log_queue):
    logger.setup_worker_logger(log_queue)

    if not utils.if_active("lod2"):
        return

    base_path = config.get_path(["loader", "sources", "lod2", "path", "lod2"])
    os.makedirs(base_path, exist_ok=True)

    for ags in config.get_list(["loader", "scope"]):
        # Run aria2c to download the file (equivalent to `aria2c <url>`)
        url = config.get_value(["loader", "sources", "lod2", "url"])
        if isinstance(url, list):
            url = (" ").join(url)
        url = url.replace("#scope", ags)

        gml_path = config.get_path(["loader", "sources", "lod2", "path", "gml"])
        log.info("*.gml imported from: " + gml_path + " ...")
        cmd = f"aria2c --continue=true --allow-overwrite=false --auto-file-renaming=false {url} -d {gml_path}"
        utils.do_cmd(cmd)

    # Run citydb tool to import the downloaded GML files
    params = utils.get_db_parameters("citydb")

    cmd = [
        "citydb import citygml",
        "-H", params["host"],
        "-d", params["db"],
        "-u", params["user"],
        "-p", params["password"],
        "-P", str(params["exposed_port"]),
        "--import-mode=delete", # deletes existing data before import # skip as alternative
        str(gml_path)
    ]
    cmd_str = " ".join(str(arg) for arg in cmd)
    utils.do_cmd(cmd_str)

    log.info(f"LOD2 data loaded successfully")