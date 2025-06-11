import re
import yaml
import os
from sqlalchemy import create_engine


def __load_config(path: str):
    config = {}

    if os.path.exists(path):
        with open(path, "r") as file:
            return yaml.safe_load(file) or {}

    return config


def __load_configs():
    configs = {}
    base_path = os.path.join("configs", "config.yml")

    if os.path.exists(base_path):
        with open(base_path, "r") as file:
            configs.update(yaml.safe_load(file) or {})

    # Load sub configs defined under config.yaml configs field
    for config_path in configs.get("configs", []):
        full_path = os.path.join("configs", config_path)
        configs.update(__load_config(full_path))

    return configs


# We can load config once and then use,
# otherwise we would need to do I/O operations multiple times
CONFIG = __load_configs()


def get_value(keys):
    if not keys:
        raise ValueError("keys must be a non-empty list")

    element = CONFIG
    for key in keys:
        if key not in element:
            raise KeyError(f"Key '{key}' not found in configuration.")

        element = element.get(key, {})

    # Check if element is list
    if isinstance(element, str):
        value = replace_placeholders(element, CONFIG)
    elif isinstance(element, list):
        value = [replace_placeholders(value, CONFIG) for value in element]
    else:
        value = element

    return value


def get_path(keys):
    path = get_value(keys)
    if not os.path.isabs(path):
        path = os.path.join(get_root_path(), path)
    path = os.path.abspath(path)
    return path


def get_root_path():
    # Get project root path
    root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return root_path


# Function to flatten json configuration to single level dict
def flatten_config(config):
    flat_dict = {}

    def flatten_recursive(data):
        for k, v in data.items():
            key = k
            if isinstance(v, dict):
                flatten_recursive(v)
            else:
                flat_dict[key] = v
        return flat_dict
    return flatten_recursive(config)


def replace_placeholders(path, config):
    """
    Replaces placeholders in a given path string with values from a configuration dictionary.
    """
    # Convert nested dictionary into a flat dictionary for easy lookup
    variables = flatten_config(config)

    def replacer(match):
        """
        Callback function for re.sub to replace placeholders with corresponding values.

        Raises:
            KeyError: If the placeholder is missing from the config.
        """
        key = match.group(1)  # Extract the placeholder name
        if key not in variables:
            raise KeyError(f"Missing placeholder: {key}")
        return variables[key]

    # Replace placeholders iteratively until none remain
    while re.search(r"\{(\w+)\}", path):
        path = re.sub(r"\{(\w+)\}", replacer, path)

    # Normalize the final path to remove redundant separators and up-level references
    return path


def get_db_config(service_name: str):
    if service_name not in ["citydb", "timescaledb"]:
        raise ValueError(f"Unsupported service: {service_name}")

    host = get_value(["services", service_name, "host"])
    port = get_value(["services", service_name, "port"])
    user = get_value(["services", service_name, "user"])
    password = get_value(["services", service_name, "password"])
    db = get_value(["services", service_name, "db"])

    return host, port, user, password, db


def get_db_engine(service_name: str):
    host, port, user, password, db = get_db_config(service_name)
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return create_engine(db_url)


# Create engines
citydb_engine = get_db_engine("citydb")
timescale_engine = get_db_engine("timescaledb")
