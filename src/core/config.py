import os
import re
import yaml
from copy import deepcopy


def __load_config(path: str):
    config = {}

    if os.path.exists(path):
        with open(path, "r") as file:
            return yaml.safe_load(file)

    return config


def __load_configs():
    base_path = os.path.join(get_root_path(), "configs", "config.yml")
    print(base_path)
    print(os.listdir(os.path.dirname(base_path)))

    # first get the base config
    configs = __load_config(base_path)
    print(configs)

    # Load sub configs defined under config.yaml configs field
    for config_path in configs.get("configs", []):
        full_path = os.path.join(get_root_path(), "configs", config_path)
        configs.update(__load_config(full_path))

    # Resolve placeholders in the config
    resolved_configs = resolve_yaml_placeholders(configs)

    return resolved_configs


def get_value(keys):
    if not keys:
        raise ValueError("keys must be a non-empty list")

    config = get_config()

    element = config
    for key in keys:
        if key not in element:
            raise KeyError(f"Key '{key}' not found in configuration.")

        element = element.get(key, {})

    return element


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


def flatten_dict(d, parent_key=''):
    """Flatten nested dictionary with keys joined by /."""
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}/{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key))
        else:
            items[new_key] = v
    return items


def replace_placeholders(data, flat_map):
    """Recursively replace placeholders like {a/b} using flat_map."""
    if isinstance(data, dict):
        return {k: replace_placeholders(v, flat_map) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_placeholders(item, flat_map) for item in data]
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


def resolve_yaml_placeholders(yaml_data: dict) -> dict:
    """Resolve {a/b} placeholders in a YAML dictionary."""
    flat_map = flatten_dict(yaml_data)
    resolved = replace_placeholders(deepcopy(yaml_data), flat_map)
    return resolved


def get_config():
    # We can load config once and then use,
    # otherwise we would need to do I/O operations multiple times
    config = __load_configs()
    return config
