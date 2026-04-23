from infdb import InfDB

from . import utils


def load(infdb: InfDB) -> None:
    """Downloads and unpacks the opendata package using the loader configuration.

    Behavior preserved:
    - Reads paths and URL from the 'loader' tool config.
    - Downloads the archive to the base path, then unzips into the processed path.
    """
    log = infdb.get_worker_logger()
    # Use loader config via infdb_package
    try:
        # Download opendata package
        TOOL_NAME = infdb.get_toolname()
        archive_path = infdb.get_config_path([TOOL_NAME, "sources", "package", "path", "base"], type="loader")
        url = infdb.get_config_value([TOOL_NAME, "sources", "package", "url"])
        log.info("Download opendata package from %s to %s", url, archive_path)
        utils.download_files(url, archive_path, infdb)

        # Unzip opendata package
        file_path = utils.get_file(archive_path, filename="opendata", ending=".zip", infdb=infdb)
        opendata_path = infdb.get_config_path([TOOL_NAME, "sources", "package", "path", "processed"], type="loader")
        log.info("Unzip opendata package from %s to %s", file_path, opendata_path)
        utils.unzip(file_path, opendata_path, infdb)

        log.info("package done!")
    except Exception as err:
        log.exception("An error occurred while processing PACKAGE data: %s", str(err))
