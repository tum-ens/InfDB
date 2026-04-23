import logging
import multiprocessing
import os
import sys
from logging.handlers import QueueHandler, QueueListener

# ============================== Constants ==============================

LOGGER_NAME: str = "infdb"
WORKER_LOGGER_NAME: str = "infdb.worker"
LOG_FORMAT: str = "%(asctime)s | %(processName)s [ %(process)d] | %(levelname)s: %(message)s"
FILE_ENCODING: str = "utf-8"


class InfdbLogger:
    """Console + file logging with a multiprocessing-safe queue listener."""

    def __init__(self, log_path: str, level: str = "INFO", cleanup: bool = False) -> None:
        """Initializes the root logger, handlers, and a QueueListener.

        Args:
            log_path: Path to the log file to write.
            level: Logging level name (e.g., 'INFO', 'DEBUG').
            cleanup: If True, remove any existing log file at `log_path` before starting.
        """
        self.formatter = logging.Formatter(LOG_FORMAT)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.formatter)

        # Ensure log directory exists
        log_dir = os.path.dirname(log_path)
        if log_dir:  # non-empty (i.e. path has a directory component)
            os.makedirs(log_dir, exist_ok=True)

        # Optional cleanup of existing log file
        if cleanup:
            try:
                if os.path.exists(log_path):
                    os.remove(log_path)
            except Exception as exc:
                # Infdb logger not fully initialized yet, use default logging
                logging.exception("Exception occurred during __init__(): %s", exc)

        # File handler
        file_handler = logging.FileHandler(log_path, encoding=FILE_ENCODING)
        file_handler.setFormatter(self.formatter)

        # Root logger
        self.root_logger = logging.getLogger(LOGGER_NAME)
        self.root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self.root_logger.handlers.clear()
        self.root_logger.addHandler(console_handler)
        self.root_logger.addHandler(file_handler)

        # Queue + listener for worker process logs
        self.log_queue: multiprocessing.Queue = multiprocessing.Queue()
        self.listener = QueueListener(self.log_queue, console_handler, file_handler)
        self.listener.start()

    def stop(self):
        """Flushes and stops the QueueListener."""
        self.root_logger.info("Shutting down infdb log listener...")
        try:
            self.listener.stop()
        except Exception as exc:
            # Infdb logger may be partially torn down, use default logging
            logging.exception("Exception occurred during __stop__(): %s", exc)

    def setup_worker_logger(self) -> logging.Logger:
        """Creates a logger for worker processes that forwards to the queue.

        Returns:
            A logger configured with a QueueHandler that sends records to the root listener.
        """
        logger = logging.getLogger(WORKER_LOGGER_NAME)
        logger.setLevel(self.root_logger.level)
        logger.handlers.clear()
        logger.addHandler(QueueHandler(self.log_queue))
        logger.propagate = False
        return logger
