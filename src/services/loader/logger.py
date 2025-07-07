import logging
import sys


def init_logger(name, filename):
    logger = logging.getLogger(name)
    # logger.setLevel(logging.DEBUG)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s;%(levelno)s %(processName)s; %(filename)s: %(funcName)s - %(levelname)s: %(message)s')

    # Logging to file
    file_handler = logging.FileHandler(filename)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Logging to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def get_logger(name):
    logger = logging.getLogger(name)
    return logger
