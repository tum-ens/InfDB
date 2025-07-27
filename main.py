import multiprocessing as mp
from src import utils
from tools.loader import env
from src import bkg , basemap, lod2, census2022, plz
from src.logger import setup_main_logger
import multiprocessing
import logging

log = logging.getLogger(__name__)

if __name__ == "__main__":

    log_queue = multiprocessing.Queue()
    listener = setup_main_logger(log_queue)

    log.info("Starting loader...")

    # Ensure that administrative areas are
    bkg.load_envelop()

    # Load NUTS Regions beforehand as basis
    # Load remaining data in parallel
    mp.freeze_support()
    processes = []
    processes.append(mp.Process(target=bkg.load, args=(log_queue,)))
    processes.append(mp.Process(target=lod2.load, args=(log_queue,)))
    processes.append(mp.Process(target=plz.load, args=(log_queue,)))
    processes.append(mp.Process(target=basemap.load, args=(log_queue,)))
    processes.append(mp.Process(target=census2022.load, args=(log_queue,)))

    for process in processes:
        process.start()
        if not utils.if_multiproccesing():
            print("hallo!!!")
            #processes.join()    # Only one process at a time
    log.info("Processes started")

    # Wait for processes
    for process in processes:
        process.join()

    listener.stop()

    log.info("Processes done")



