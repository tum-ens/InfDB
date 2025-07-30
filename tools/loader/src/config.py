import logging
import os
import re
import yaml
from copy import deepcopy
from dotenv import load_dotenv

log = logging.getLogger(__name__)

def _load_config(path: str):
    if os.path.exists(path):
        with open(path, "r") as file:
            return yaml.safe_load(file)
    else:
        log.error(f"Configuration file '{path}' does not exist.")
        return None


def _merge_configs():
    base_path = os.path.join("configs", "config-loader.yml")    # hardcoded in compose.yml btw. .env file
    logging.debug(f"Loading configuration from '{base_path}'")
    logging.debug(f"File in '{base_path}': '{os.listdir(os.path.dirname(base_path))}'")

    # first get the base config
    configs = _load_config(base_path)

    # Load sub configs defined under config.yaml configs field
    filename = configs["loader"]["config-infdb"]
    path_infdb_config = os.path.join("configs-infdb", filename) # hardcoded in compose.yml btw. env file

    log.debug(f"Loading configuration from '{path_infdb_config}'")
    if os.path.exists(path_infdb_config):
        configs.update(_load_config(path_infdb_config))
    else:
        log.error(f"Failed to load {path_infdb_config}")

    # Resolve placeholders in the config
    config_resolved = _resolve_yaml_placeholders(configs)
    return config_resolved


def get_value(keys):
    if not keys:
        raise ValueError("keys must be a non-empty list")

    config = get_config()

    element = config
    for key in keys:
        if key not in element:
            log.error(f"Key '{key}' not found in configuration.")
            return None

        element = element.get(key, {})

    return element


def get_path(keys):
    path = get_value(keys)
    if not os.path.isabs(path):
        path = os.path.join("/tools/loader/data-loader", path)
    path = os.path.abspath(path)
    return path


def get_root_path():
    # Get project root path
    root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return root_path


def _flatten_dict(d, parent_key='', sep="/"):
    """Flatten nested dictionary with keys joined by /."""
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(_flatten_dict(v, parent_key=new_key, sep=sep))
        else:
            items[new_key] = v
    return items


def _replace_placeholders(data, flat_map):
    """Recursively replace placeholders like {a/b} using flat_map."""
    if isinstance(data, dict):
        return {k: _replace_placeholders(v, flat_map) for k, v in data.items()}
    elif isinstance(data, list):
        return [_replace_placeholders(item, flat_map) for item in data]
    elif isinstance(data, str):
        pattern = re.compile(r'{([^{}]+)}')
        while True:
            match = pattern.search(data)
            if not match:
                break
            key = match.group(1)
            replacement = flat_map.get(key)
            if replacement is None:
                break  # unresolved
            data = data.replace(f"{{{key}}}", str(replacement))
        return data
    else:
        return data


def _resolve_yaml_placeholders(yaml_data: dict) -> dict:
    """Resolve {a/b} placeholders in a YAML dictionary."""
    flat_map = _flatten_dict(yaml_data)
    resolved = _replace_placeholders(deepcopy(yaml_data), flat_map)
    return resolved


def get_config():
    # We can load config once and then use,
    config = _CONFIG
    return config


def write_yaml(output_yaml, output_path):
    output_path = os.path.join(get_root_path(), output_path)
    with open(output_path, "w") as f:
        yaml.dump(output_yaml, f, default_flow_style=False, sort_keys=False)

_CONFIG = _merge_configs()