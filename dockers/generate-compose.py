import yaml
import os
from src.core.config import get_value

base_dir = os.path.dirname(__file__)
config_services_path = os.path.join(base_dir, "..", "configs/config-services.yml")

#This function writes configuration for services into a .env file which then be read by the containers.
def write_env_file(file_path=".env"):
    with open(config_services_path) as f:
        config = yaml.safe_load(f)

    with open(file_path, "w") as f:
        for service_name, props in config["services"].items():
            if isinstance(props, dict) and props.get("status") == "active":
                for key, _value in props.items():
                    f.write(f"{(service_name + '_' + key).upper()}={get_value(['services', service_name, key])}\n")
        network_name=get_value(["base", "network_name"])
        f.write(f"NETWORK_NAME={network_name}\n")

#This function auto generates the docker compose file for us.
def write_compose_file():
    output_path = os.path.join(base_dir, "docker-compose.yml")

    with open(config_services_path) as f:
        config = yaml.safe_load(f)

    output = {
        "name": "infdb",
        "include": ['./loader.yml'], # loader by default should exists
        "volumes": {
            "timescale_data": None,
            "citydb_data": None,
            "citydb_data_v4": None,
            "pgadmin_data": None
        },
        "networks": {
            get_value(["base", "network_name"]): {
                "driver": "bridge"
            }
        }
    }

    for service_name, props in config["services"].items():
        if props.get("status") == "active":
            output["include"].append(f"./{service_name}.yml")

    with open(output_path, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)


write_env_file("./dockers/.env")
write_compose_file()


