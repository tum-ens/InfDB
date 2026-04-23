import logging
from typing import Any, Dict, List, Optional

from .client import InfdbClient
from .config import InfdbConfig
from .logger import InfdbLogger


class InfDB:
    """Facade for configuration, logging, and DB connections for InfDB.

    Other repos (e.g., `infdb-import`, `infdb-basedata`) should import and use this
    class as the single entry point.
    """

    def __init__(self, tool_name: str, config_path: str = None, host: str = None) -> None:
        """Initializes the facade with configuration and logging.

        Args:
            tool_name: Identifier used to pick the tool section in the config.
            config_path: Path to the YAML configuration file.
            host: The host address for the database connection.
        """
        self.tool_name: str = tool_name
        self.config_path: str = config_path
        self.host: str = host

        # Load configuration
        self.infdbconfig: InfdbConfig = InfdbConfig(tool_name=self.tool_name, config_path=self.config_path, host=self.host)

        # Initialize logging from config, with safe fallbacks
        DEFAULT_LOG_FILE: str = f"{self.tool_name}.log"
        log_path = self.get_config_value(["logging", "path"], insert_toolname=True) or DEFAULT_LOG_FILE
        DEFAULT_LOG_LEVEL: str = "INFO"
        level = self.get_config_value(["logging", "level"], insert_toolname=True) or DEFAULT_LOG_LEVEL
        self.infdblogger: InfdbLogger = InfdbLogger(log_path=log_path, level=level)
        self.logger: logging.Logger = self.infdblogger.root_logger

    def __str__(self) -> str:
        """Returns a string description of the InfDB facade."""
        return f"InfDB(tool='{self.tool_name}', config='{self.config_path}')"

    # ------------------ config & logging helpers ------------------

    def get_logger(self) -> logging.Logger:
        """Returns the root logger used by this instance."""
        return self.logger

    def get_worker_logger(self) -> logging.Logger:
        """Creates and returns a worker logger from the InfdbLogger helper."""
        return self.infdblogger.setup_worker_logger()

    def stop_logger(self) -> None:
        """Stops the InfdbLogger's QueueListener."""
        self.infdblogger.stop()

    # ------------------ database helpers ------------------

    def connect(self) -> InfdbClient:
        """Creates a new database client.

        Prefer: `with inf.connect(...) as client: ...`.

        Args: None

        Returns:
            An InfdbClient connected to the requested database.
        """
        return InfdbClient(self.infdbconfig, self.get_logger())

    def get_db_engine(self):
        """Returns a SQLAlchemy engine for the specified database.

        Args: None

        Returns:
            A SQLAlchemy Engine instance connected to the same target DB.
        """
        with self.connect() as client:
            return client.get_db_engine()

    # ------------------ configuration access ------------------

    def get_toolname(self) -> str:
        """Returns the tool name configured for this instance."""
        return self.tool_name

    def get_config_dict(self) -> Dict[str, Any]:
        """Returns the merged configuration dictionary."""
        return self.infdbconfig.get_config()

    def get_db_parameters_dict(self) -> Dict[str, Any]:
        """Returns final parameters dictionary for the postgres service."""
        return self.infdbconfig.get_db_parameters()

    def get_config_value(self, keys: List[str], insert_toolname: bool = False):
        """Returns a value from the configuration by traversing a key path.

        Args:
            keys: Ordered key path within the configuration.
            insert_toolname: If True, prepend the tool name to the key path.

        Returns:
            The value at the specified path, or None if missing.
        """
        keys = list(keys)
        if insert_toolname:
            keys.insert(0, self.tool_name)
        return self.infdbconfig.get_value(keys)

    def get_config_path(self, keys: List[str], type: str = "config", insert_toolname: bool = False) -> str:
        """Resolves a filesystem path from config.

        Args:
            keys: Ordered key path within the configuration.
            insert_toolname: If True, prepend the tool name to the key path.

        Returns:
            An absolute filesystem path.
        """
        keys = list(keys)
        if insert_toolname:
            keys.insert(0, self.tool_name)
        return self.infdbconfig.get_path(keys, type=type)

    def get_env_variable(self, key) -> Optional[str]:
        """Returns a dictionary of environment variables for this tool.

        Returns:
            A dictionary of environment variables.
        """
        return self.infdbconfig.get_env_parameters(key=key)
