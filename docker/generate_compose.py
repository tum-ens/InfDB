import yaml
import os
from CONFIG import config, write_env_file

base_dir = os.path.dirname(__file__)
config_path = os.path.join(base_dir, "..", "CONFIG.yaml")
output_path = os.path.join(base_dir, "docker-compose.yaml")

write_env_file(config, ".env")
write_env_file(config, "../.env")

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
