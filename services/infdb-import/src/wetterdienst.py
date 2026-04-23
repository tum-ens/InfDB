import logging
import multiprocessing as mp
from datetime import datetime
from logging.handlers import QueueHandler
from typing import Final, Tuple
from zoneinfo import ZoneInfo

from wetterdienst.provider.dwd.observation import DwdObservationRequest

from . import utils

# ============================== Constants ==============================

LOGGER_NAME: Final[str] = __name__
TOOL_NAME: Final[str] = "openmeteo"
TZ_UTC: Final[ZoneInfo] = ZoneInfo("UTC")
CRS_WGS84_EPSG: Final[int] = 4326
BBOX_PRINT_LABEL: Final[str] = "Filter by bbox (Frankfurt)"
ALL_STATIONS_PRINT_LABEL: Final[str] = "All stations"
FRANKFURT_COORDS: Final[Tuple[float, float]] = (50.11, 8.68)
START_DATE_UTC: Final[datetime] = datetime(2020, 1, 1, tzinfo=TZ_UTC)
END_DATE_UTC: Final[datetime] = datetime(2020, 1, 20, tzinfo=TZ_UTC)


# Module logger
log = logging.getLogger(LOGGER_NAME)


def _setup_worker_logger(log_queue: mp.Queue) -> logging.Logger:
    """Sends this module's logs to the main process QueueListener.

    Args:
        log_queue: Multiprocessing queue used by the central QueueListener.

    Returns:
        Configured module logger.
    """
    logger = logging.getLogger(LOGGER_NAME)
    base = logging.getLogger("infdb")
    logger.setLevel(base.level if base.handlers else logging.INFO)
    logger.handlers.clear()
    logger.addHandler(QueueHandler(log_queue))
    logger.propagate = False
    return logger


def load(log_queue: mp.Queue) -> None:
    """Entry point preserved: uses 'openmeteo' feature flag and prints success message."""
    _setup_worker_logger(log_queue)

    if not utils.if_active(TOOL_NAME):
        return

    stations_filter_by_examples()

    log.info("Openmeteo data loaded successfully")


def stations_filter_by_examples() -> None:
    """Retrieves DWD stations that measure air temperature; prints demo outputs."""
    request = DwdObservationRequest(
        parameters=("hourly", "temperature_air"),
        periods="recent",
        start_date=START_DATE_UTC,
        end_date=END_DATE_UTC,
    )

    print(ALL_STATIONS_PRINT_LABEL)
    print(request.all().df)

    print(BBOX_PRINT_LABEL)
    envelop = utils.get_envelop()
    xmin, ymin, xmax, ymax = envelop.to_crs(CRS_WGS84_EPSG).total_bounds
    stations = request.filter_by_bbox(xmin, ymin, xmax, ymax)
    df_bbox = stations.df
    print(df_bbox)

    values_bbox_all = stations.values.all()
    _ = values_bbox_all

    values_interpolated = request.interpolate(FRANKFURT_COORDS)
    print(values_interpolated)
