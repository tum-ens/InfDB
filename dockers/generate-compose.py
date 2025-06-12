import yaml
import os
from src.core.config import get_value, CONFIG

base_dir = os.path.dirname(__file__)

#This function writes configuration for services into a .env file which then be read by the containers.
def write_env_file(file_path=".env"):
    services = CONFIG.get("services", {})

    with open(file_path, "w") as f:
        for service_name, props in services.items():
            if isinstance(props, dict) and props.get("status") == "active":
                for key in props:
                    env_key = f"{service_name}_{key}".upper()
                    value = get_value(["services", service_name, key])
                    f.write(f"{env_key}={value}\n")

        loader_dir = get_value(["loader", "loader_dir"])
        f.write(f"LOADER_DIR={loader_dir}\n")
        network_name = get_value(["base", "network_name"])
        f.write(f"NETWORK_NAME={network_name}\n")

#This function auto generates the docker compose file for us.
def write_compose_file():
    output_path = os.path.join(base_dir, "docker-compose.yml")

    output = {
        "name": "infdb",
        "include": ["./loader.yml"],  # default loader
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

    services = CONFIG.get("services", {})
    for service_name, props in services.items():
        if isinstance(props, dict) and props.get("status") == "active":
            output["include"].append(f"./{service_name}.yml")

    with open(output_path, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)


write_env_file("./dockers/.env")
write_compose_file()


