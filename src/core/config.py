import re
import yaml
import glob
import os


def get_root_path():
    # Get project root path
    root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return root_path


def __load_configs():
    # Merges config files as they might have placeholder dependencies in between at this step.
    # for example having general.base_dir
    configs = {}
    for path in glob.glob("./configs/*.yaml"):
        with open(path, "r") as file:
            config_part = yaml.safe_load(file) or {}
            configs.update(config_part)

    return configs


def get_value(keys):
    config = __load_configs()
    # Get nested element along keys
    element = config
    for key in keys:
        if key not in element:
            raise KeyError(f"Key '{key}' not found in configuration.")

        element = element.get(key, {})

    # Check if element is list
    if isinstance(element, str):
        value = replace_placeholders(element, config)
    elif isinstance(element, list):
        value = [replace_placeholders(value, config) for value in element]
    else:
        value = element

    return value


def get_path(keys):
    path = get_value(keys)
    if not os.path.isabs(path):
        path = os.path.join(get_root_path(), path)
    path = os.path.abspath(path)
    print(path)
    return path


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
