from . import config, utils
import logging

log = logging.getLogger(__name__)

def load():
    # Download opendata package
    archive_path = config.get_path(["loader", "sources", "package", "path", "base"])             
    url = config.get_value(["loader", "sources", "package", "url"])
    log.info(f"Download opendata package from {url} to {archive_path}")

    # file = utils.download_files(url, archive_path)
    file = utils.download_files(url, archive_path)

    # Unzip opendata package
    opendata_path = config.get_path(["loader", "sources", "package", "path", "processed"])
    log.info(f"Unzip opendata package to {opendata_path}")
    utils.unzip(file, opendata_path)
    
    log.info("package done!")