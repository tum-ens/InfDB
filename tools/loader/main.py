import multiprocessing as mp
import sys

from src import utils
from src import bkg, basemap, lod2, census2022, plz, tabula
from src.logger import setup_main_logger
import multiprocessing
import logging

log = logging.getLogger(__name__)

if __name__ == "__main__":

    log_queue = multiprocessing.Queue()
    listener = setup_main_logger(log_queue)

    log.info("Starting loader.............................................")
    log.info("-------------------------------------------------------------")
    log.info("-------------------------------------------------------------")

    # Ensure that administrative areas are
    bkg.load_envelop()

    # Load data in parallel
    mp.freeze_support()
    processes = []
    processes.append(mp.Process(target=tabula.load, args=(log_queue,), name="tabula"))
    processes.append(mp.Process(target=bkg.load, args=(log_queue,), name="bkg"))
    processes.append(mp.Process(target=lod2.load, args=(log_queue,), name="lod2"))
    processes.append(mp.Process(target=plz.load, args=(log_queue,), name="plz"))
    processes.append(mp.Process(target=basemap.load, args=(log_queue,), name="basemap"))
    processes.append(mp.Process(target=census2022.load, args=(log_queue,), name="census2022"))

    for process in processes:
        process.start()
        if not utils.if_multiproccesing():
            processes.join()    # Only one process at a time
            log.info("Process %s done", process.name)
    log.info("Processes started")

    # Wait for processes
    for cnt, process in enumerate(processes, 1):
        process.join()
        log.info("Process %s done (%d out of %d)", process.name, cnt, len(processes))

    listener.stop()

    log.info("Processes done")
