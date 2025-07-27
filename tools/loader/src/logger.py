import logging
import os
from logging.handlers import QueueHandler, QueueListener
import sys
from . import config

def setup_main_logger(log_queue):
    formatter = logging.Formatter('%(asctime)s | %(processName)s | %(levelname)s: %(message)s')

    # Logging to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Logging to file
    file_path = config.get_value(["loader", "logging", "path"])
    # if os.path.exists(file_path):
    #     os.remove(file_path)    # for debugging
    file_handler = logging.FileHandler(file_path)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    level_string = config.get_value(["loader", "logging", "level"])
    level = logging._nameToLevel.get(level_string.upper(), logging.INFO)
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    listener = QueueListener(log_queue, console_handler, file_handler)
    listener.start()
    return listener


def setup_worker_logger(log_queue):
    root_logger = logging.getLogger()
    level_string = config.get_value(["loader", "logging", "level"])
    level = logging._nameToLevel.get(level_string.upper(), logging.INFO)
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(QueueHandler(log_queue))
    root_logger.propagate = False

# import logging
# import multiprocessing
# import time
#
# def worker(log_queue):
#     logger = logging.getLogger("worker")
#     logger.addHandler(logging.handlers.QueueHandler(log_queue))
#     logger.setLevel(logging.DEBUG)
#     logger.info(f"Worker started in PID {multiprocessing.current_process().pid}")
#
# def configure_logger(log_queue):
#     handler = logging.StreamHandler()
#     formatter = logging.Formatter('%(asctime)s %(processName)s %(levelname)s: %(message)s')
#     handler.setFormatter(formatter)
#
#     root_logger = logging.getLogger()
#     root_logger.setLevel(logging.DEBUG)
#     root_logger.addHandler(handler)
#
#     listener = logging.handlers.QueueListener(log_queue, handler)
#     return listener

# import logging
# import multiprocessing
# import sys
#
# def get_logger(name="loader"):
#
#     logger = logging.getLogger(name)
#     return logger
#
#
# def init_logger(name="loader", level_string="Info", file_path="loader.log"):
#     logger = logging.getLogger(name)
#
#     # Set debug level
#     level = logging._nameToLevel.get(level_string.upper(), logging.INFO)   # Fallback to level "INFO"
#     logger.setLevel(level)
#     logger.propagate = False
#
#     # Format output
#     formatter = logging.Formatter('%(asctime)s;%(levelno)s %(processName)s; %(filename)s: %(funcName)s - %(levelname)s: %(message)s')
#
#     if logger.hasHandlers():
#         logger.handlers.clear()
#
#     if not logger.hasHandlers():
#         # Logging to console
#         console_handler = logging.StreamHandler(sys.stdout)
#         console_handler.setFormatter(formatter)
#         logger.addHandler(console_handler)
#
#         # Logging to file
#         file_handler = logging.FileHandler(file_path)
#         file_handler.setFormatter(formatter)
#         logger.addHandler(file_handler)
#
#     return logger
