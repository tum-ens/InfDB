import yaml
import os
from src.core.config import CONFIG, get_value

base_dir = os.path.dirname(__file__)
input_path = os.path.join(base_dir, "../../configs/config-sunpot.yml")
file_path = os.path.join(base_dir, ".env")

def generate_env():
    """
    Writes all uppercase keys and loader/sunset directories from the config YAML into a .env file.
    """
    with open(input_path, "r") as f:
        config = yaml.safe_load(f)

    with open(file_path, "w") as f:
        # Write all UPPERCASE top-level keys
        for key, value in config.items():
            if key.isupper():
                f.write(f"{key}={value}\n")
        
        # Write loader dir
        loader_dir = get_value(["loader", "loader_dir"])
        f.write(f"LOADER_DIR={loader_dir}\n")

        # Write sunset dir
        sunset_dir = get_value(["base", "base_sunset_dir"])
        f.write(f"SUNSET_DIR={sunset_dir}\n")

generate_env()
