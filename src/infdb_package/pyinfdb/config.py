import logging
import os
import re
from copy import deepcopy
from typing import Any, Dict, List, Optional

import yaml

# ============================== Constants ==============================

CONFIG_FILE_TEMPLATE: str = "config-{tool}.yml"
DATA_BASE_DIR: str = os.path.join("..", "data")
SETUP_BASE_DIR: str = "."
FILE_ENCODING: str = "utf-8"


class InfdbConfig:
    """Read and resolve tool-specific YAML config with optional InfDB base merge."""

    def __init__(self, tool_name: str, config_path: str, host: str = None) -> None:
        """Initializes the configuration for a tool.

        Args:
            tool_name: The tool identifier (used to select the YAML file and section).
            config_path: Path to the configuration file.
            host: The host address for the database connection.
        """
        self.tool_name: str = tool_name
        self.log: logging.Logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.host = host
        self._CONFIG: Dict[str, Any] = self._load_config(self.config_path)

    def __str__(self) -> str:
        """Returns a string representation of the InfdbConfig."""
        return f"InfdbConfig(tool='{self.tool_name}', path='{self.config_path}', host='{self.host}')"

    # ---------------- internal helpers ----------------

    def _load_config(self, path: str) -> Dict[str, Any]:
        """Loads a YAML file. Raises FileNotFoundError if the file is missing."""
        if path:
            if os.path.exists(path):
                with open(path, "r", encoding=FILE_ENCODING) as file:
                    configs = yaml.safe_load(file) or {}
            else:
                self.log.debug("Config file '%s' not found.", path)
                raise FileNotFoundError(f"Config file '{path}' not found.")
        else:
            self.log.debug("No config path provided.")
            configs = {}

        return self._resolve_yaml_placeholders(configs)


    def _flatten_dict(self, data: Dict[str, Any], parent_key: str = "", sep: str = "/") -> Dict[str, Any]:
        """Flattens nested dictionaries into path-like keys."""
        items: Dict[str, Any] = {}
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(value, dict):
                items.update(self._flatten_dict(value, parent_key=new_key, sep=sep))
            else:
                items[new_key] = value
        return items

    def _replace_placeholders(self, data: Any, flat_map: Dict[str, Any]) -> Any:
        """Recursively replaces {placeholders} in strings using a flattened map."""
        if isinstance(data, dict):
            return {k: self._replace_placeholders(v, flat_map) for k, v in data.items()}
        if isinstance(data, list):
            return [self._replace_placeholders(item, flat_map) for item in data]
        if isinstance(data, str):
            pattern = re.compile(r"{([^{}]+)}")
            out = data
            while True:
                match = pattern.search(out)
                if not match:
                    break
                key = match.group(1)
                replacement = flat_map.get(key)
                if replacement is None:
                    break
                out = out.replace(f"{{{key}}}", str(replacement))
            return out
        return data

    def _resolve_yaml_placeholders(self, yaml_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolves intra-file {placeholders} using flattened key/value paths."""
        flat_map = self._flatten_dict(yaml_data)
        return self._replace_placeholders(deepcopy(yaml_data), flat_map)

    # ---------------- public API ----------------

    def get_config(self) -> Dict[str, Any]:
        """Returns the fully merged and resolved configuration dictionary."""
        return self._CONFIG

    def get_value(self, keys: List[str]) -> Any:
        """Safely traverses nested keys; returns None if the path is missing.

        Args:
            keys: Ordered key path within the configuration.

        Returns:
            The value at the specified path, or None if any segment is missing.

        Raises:
            ValueError: If keys is empty.
        """
        if not keys:
            raise ValueError("keys must be a non-empty list")
        element: Any = self.get_config()
        for key in keys:
            if not isinstance(element, dict) or key not in element:
                return None
            element = element.get(key, {})
        return element

    def get_path(self, keys: List[str], type: str) -> str:
        """Resolves a path from config and maps it to a filesystem location.

        Args:
            keys: Ordered key path within the configuration.
            type: One of {'loader', 'heat', 'package', 'setup'} controlling base dir.

        Returns:
            Absolute filesystem path derived from the config value.
        """
        path = self.get_value(keys)
        if not os.path.isabs(path):
            path = os.path.join(DATA_BASE_DIR, path)  # mounted data dir within docker
        path = os.path.abspath(path)
        return path

    @staticmethod
    def get_root_path() -> str:
        """Returns the project root path (two levels up from this file)."""
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def get_db_parameters(self, db_name: str = "postgres") -> Dict[str, str]:
        """Retrieve database connection parameters for a specified service.
        
        Reads database configuration from the config-choose-a-name.yml file and merges it with
        environment variables. Environment variables take precedence if set, otherwise config
        file values are used. The host defaults to "host.docker.internal" if not specified.
        
        Environment variables are expected in the format: SERVICES_{DB_NAME}_{PARAMETER}
        (e.g., SERVICES_POSTGRES_PORT, SERVICES_POSTGRES_USER)
        
            db_name: Name of the database service section in the config file.
                    Defaults to "postgres".
        
            Dictionary containing database connection parameters with keys:
            - host: Database host address (defaults to "host.docker.internal")
            - port: Database port number
            - user: Username for authentication
            - password: Password for authentication
            - dbname: Database name
            - epsg: EPSG code for the database spatial reference system
        
        Note:
            - Config file values with "None" string are ignored in favor of environment variables
            - If neither environment variable nor config file value exists, key will be None
        """
        db_params_service = {}

        config_dict = self.get_value([self.tool_name, "hosts", db_name])

        keys = ["exposed_port", "user", "password", "db", "epsg", "host"]
        for key in keys:
            db_params_service[key] = self.get_env_parameters(f"SERVICES_{db_name.upper()}_{key.upper()}")
            if config_dict and key in config_dict and config_dict[key] != "None":
                db_params_service[key] = config_dict[key]

        # Override host with constructor argument if provided
        if self.host:
            db_params_service["host"] = self.host

        return db_params_service

    def get_env_parameters(self, key) -> Optional[str]:
        """Returns a dictionary of environment variables for this tool.

        Args:
            key: Environment variable name (case-insensitive).
            infdb: An InfDB object used for logging.

        Returns:
            A dictionary of environment variables.

        Raises:
            ValueError: If the environment variable ``key.upper()`` is not set.
        """

        env_param = os.getenv(key.upper())
        if env_param is None:
            self.log.error(f"Environment variable '{key.upper()}' is not set.")
            raise ValueError(f"Environment variable '{key.upper()}' is not set.")

        return env_param
