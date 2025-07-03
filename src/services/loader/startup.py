import multiprocessing as mp
from src.services.loader.sources import basemap, bkg, census2022, lod2, plz
import logger

logger.init_logger("infdb-loader", "infdb-loader.log")

log = logger.get_logger("infdb-loader")
log.info("Starting loader...")


# Load NUTS Regions beforehand as basis
#bkg.load()
#basemap.load()
#plz.load()
#census2022.load()
lod2.load()

# Load remaining data in parallel
processes = []
# processes.append(mp.Process(target=lod2.load()))
# processes.append(mp.Process(target=census2022.load()))
# processes.append(mp.Process(target=plz.load()))
# processes.append(mp.Process(target=basemap.load()))

# for process in processes:
#     process.start()
# print("Loader started")
#
# # Wait for processes
# for process in processes:
#     process.join()
# print("Done")
