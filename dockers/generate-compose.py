import yaml
import os
from src.core.config import get_value
from src.core import config
import json

base_dir = os.path.dirname(__file__)


## This function writes configuration for services into a .env file which then be read by the containers.
def write_env_file(file_path=".env"):
    services = config.get_value(["services"])

    with open(file_path, "w") as f:
        for service_name, props in services.items():
            if isinstance(props, dict) and props.get("status") == "active":
                for key in props:
                    env_key = f"{service_name}_{key}".upper()
                    value = get_value(["services", service_name, key])
                    f.write(f"{env_key}={value}\n")

        loader_dir = get_value(["base", "path", "base"])
        f.write(f"LOADER_DIR={loader_dir}\n")
        network_name = get_value(["base", "network_name"])
        f.write(f"NETWORK_NAME={network_name}\n")
        gml_dir = get_value(["loader", "sources", "lod2", "path", "gml"])
        f.write(f"GML_DIR={gml_dir}\n")


## This function auto generates the docker compose file for us.
def write_compose_file():
    output_path = os.path.join(base_dir, "docker-compose.yml")

    output = {
        "name": "infdb",
        "include": ["./loader/loader.yml"],  # loader by default should exist
        "volumes": {
            "timescale_data": None,
            "citydb_data": None,
            "pgadmin_data": None
        },
        "networks": {
            get_value(["base", "network_name"]): {
                "driver": "bridge"
            }
        }
    }

    services = config.get_value(["services"])
    for service_name, props in services.items():
        if isinstance(props, dict) and props.get("status") == "active":
            output["include"].append(f"./services/{service_name}.yml")

    with open(output_path, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)


def setup_pgadmin_servers(output_path):
    services = config.get_value(["services"])

    servers = {
        "Servers": {}
    }

    server_id = 1

    for name, service in services.items():
        if name.lower() not in ["citydb", "timescaledb"]:
            continue

        servers["Servers"][str(server_id)] = {
            "Name": name.capitalize(),
            "Group": "Servers",
            "Host": get_value(["services", name, "host"]),
            "Port": 5432,
            "MaintenanceDB": get_value(["services", name, "db"]),
            "Username": get_value(["services", name, "user"]),
            "SSLMode": "prefer"
        }
        server_id += 1
    
    with open(output_path, "w") as f:
        json.dump(servers, f, indent=2)


write_env_file("./dockers/.env")
write_compose_file()
setup_pgadmin_servers("./dockers/services/servers.json")
