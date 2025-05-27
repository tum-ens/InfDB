import yaml
import os
from src.core.config import config

def write_env_file(file_path=".env"):
    def flatten(d, parent_key=""):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}_{k}".upper() if parent_key else k.upper()
            if isinstance(v, dict):
                items.extend(flatten(v, new_key))
            else:
                items.append((new_key, v))
        return items

    flat_config = flatten(config)

    with open(file_path, "w") as f:
        for key, value in flat_config:
            f.write(f"{key}={value}\n")


def write_compose_file():
    base_dir = os.path.dirname(__file__)
    config_path = os.path.join(base_dir, "..", "configs/config.yaml")
    output_path = os.path.join(base_dir, "docker-compose.yaml")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    output = {
        "name": "infdb",
        "include": ['./loader.yaml'],
        "volumes": {
            "timescale_data": None,
            "citydb_data": None,
            "citydb_data_v4": None,
            "pgadmin_data": None
        },
        "networks": {
            "database": {
                "name": "database_network",
                "driver": "bridge"
            }
        }
    }


    for service_name, props in config.items():
        if props.get("status") == "active":
            output["include"].append(f"./{service_name}.yaml")

    with open(output_path, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)


write_env_file("./dockers/.env")
write_compose_file()


