import yaml
import os
from src.core.config import get_value

base_dir = os.path.dirname(__file__)
config_services_path = os.path.join(base_dir, "..", "configs/config_services.yaml")

#This function writes configuration for services into a .env file which then be read by the containers.
def write_env_file(file_path=".env"):
    with open(config_services_path) as f:
        config = yaml.safe_load(f)

    with open(file_path, "w") as f:
        for service_name, props in config["services"].items():
            if isinstance(props, dict) and props.get("status") == "active":
                for key, _value in props.items():
                    f.write(f"{(service_name + '_' + key).upper()}={get_value(['services', service_name, key])}\n")
        f.write(f"NETWORK_EXTERNAL_NAME={get_value(['base', 'network_external_name'])}\n")
        f.write(f"SUNSET_DIR={get_value(['base', 'base_sunset_dir'])}\n")

#This function auto generates the docker compose file for us.
def write_compose_file():
    output_path = os.path.join(base_dir, "docker-compose.yaml")

    with open(config_services_path) as f:
        config = yaml.safe_load(f)

    output = {
        "name": "infdb",
        "include": ['./loader.yaml'], # loader by default should exists
        "volumes": {
            "timescale_data": None,
            "citydb_data": None,
            "citydb_data_v4": None,
            "pgadmin_data": None
        },
        "networks": {
            get_value(["base", "network_external_name"]): {
                "name": get_value(["base", "network_internal_name"]),
                "driver": "bridge"
            }
        }
    }

    for service_name, props in config["services"].items():
        if props.get("status") == "active":
            output["include"].append(f"./{service_name}.yaml")

    with open(output_path, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)


write_env_file("./dockers/.env")
write_compose_file()


