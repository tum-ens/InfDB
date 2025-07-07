import multiprocessing as mp
from src.services.loader.sources import basemap, bkg, census2022, lod2, plz
from src.services.loader import logger

if __name__ == "__main__":
    logger.init_logger("infdb-loader", "infdb-loader.log")

    log = logger.get_logger("infdb-loader")
    log.info("Starting loader...")

    # Load NUTS Regions beforehand as basis
    # bkg.load()
    # basemap.load()
    # plz.load()
    # census2022.load()
    # lod2.load()

    # Load remaining data in parallel
    mp.freeze_support()
    processes = []
    processes.append(mp.Process(target=lod2.load))
    processes.append(mp.Process(target=census2022.load))
    processes.append(mp.Process(target=plz.load))
    processes.append(mp.Process(target=basemap.load))
    processes.append(mp.Process(target=bkg.load))

    for process in processes:
        process.start()
    log.info("Processes started")

    # Wait for processes
    for process in processes:
        process.join()
    log.info("Processes done")
