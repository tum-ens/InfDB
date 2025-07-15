import yaml
import os
from src.core.config import get_value
from src.core import config
import json

#base_dir = os.path.dirname(__file__)

## This function writes configuration for services into a .env file which then be read by the containers.
def write_env_file(file_path=".env"):
    path = os.path.join(config.get_root_path(), file_path)
    with open(path, "w") as f:
        aa = config.get_config()
        flattened_config = config.flatten_dict(config.get_config(), sep="_")
        for key, value in flattened_config.items():
            env_key = key.upper()
            f.write(f"{env_key}={value}\n")


## This function auto generates the docker compose file for us.
def write_compose_file(output_path):

    output = {
        "name": "infdb",
        "include": [],  # loader by default should exist
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
            path = props.get("compose_file")
            output["include"].append(path)

    config.write_yaml(output, output_path)


def setup_pgadmin_servers(output_path):
    services = config.get_value(["services"])

    servers = {
        "Servers": {}
    }

    for server_id, name in enumerate(services, start=1):
        if name.lower() in ["citydb", "timescaledb"]:

            servers["Servers"][str(server_id)] = {
                "Name": name.capitalize(),
                "Group": "Servers",
                "Host": get_value(["services", name, "host"]),
                "Port": 5432,
                "MaintenanceDB": get_value(["services", name, "db"]),
                "Username": get_value(["services", name, "user"]),
                "SSLMode": "prefer"
            }

    output_path = os.path.join(config.get_root_path(), output_path)
    config.write_yaml(servers, output_path)


write_env_file(".env")
write_compose_file("docker-compose.yml")
setup_pgadmin_servers("dockers/services/servers.json")
