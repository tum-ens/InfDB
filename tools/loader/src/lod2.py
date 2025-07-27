import os
from . import config, utils, logger
import logging

log = logging.getLogger(__name__)

def load(log_queue):
    logger.setup_worker_logger(log_queue)

    if not utils.if_active("zensus_2022"):
        return

    base_path = config.get_value(["loader", "sources", "lod2", "path", "lod2"])
    os.makedirs(base_path, exist_ok=True)

    # Run aria2c to download the file (equivalent to `aria2c <url>`)
    url = config.get_value(["loader", "sources", "lod2", "url"])
    if isinstance(url, list):
        url = (" ").join(url)

    gml_path = config.get_value(["loader", "sources", "lod2", "path", "gml"])
    cmd = f"aria2c --continue=true --allow-overwrite=false --auto-file-renaming=false {url} -d {gml_path}"
    utils.do_cmd(cmd)
