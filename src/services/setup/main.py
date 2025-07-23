import os
import secrets
from src.core import config


# This function writes configuration for services into a .env file which then be read by the containers.
def write_env_file(file_path=".env"):
    path = os.path.join(config.get_root_path(), file_path)
    with open(path, "w") as f:
        flattened_config = config.flatten_dict(config.get_config(), sep="_")
        for key, value in flattened_config.items():
            env_key = key.upper()
            f.write(f"{env_key}={value}\n")
        # Add JWT secret key for QWC
        f.write("JWT_SECRET_KEY=" + secrets.token_hex(48))

# This function auto generates the docker compose file for us.
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
            config.get_value(["base", "network_name"]): {
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

import json

def setup_pgadmin_servers(output_path):
    # services = config.get_value(["services"])

    # Build pgAdmin-compatible structure
    servers_json = {"Servers": {}}
    pgpass_entries = []
    PORT = 5432

    for server_id, service in enumerate(["citydb", "timescaledb"], 1):
        servers_json["Servers"][server_id] = {
            "Name": service,
            "Group": "Servers",
            "Host": config.get_value(["services", service, "host"]),
            "Port": PORT,
            "MaintenanceDB": config.get_value(["services", service, "db"]),
            "Username": config.get_value(["services", service, "user"]),
            "SSLMode": "prefer",
            "Password": config.get_value(["services", service, "password"]),
            "PassFile": "/pgadmin4/.pgpass"
        }

        pgpass_entries.append(
            f"{config.get_value(["services", service, "host"])}:{PORT}:{service}:{config.get_value(["services", service, "user"])}:{config.get_value(["services", service, "password"])}"
        )

    # Save to servers.json
    with open(os.path.join(output_path, "servers.json"), "w") as f:
        json.dump(servers_json, f, indent=4)
    # print("servers.json with passwords written.")

    # Write .pgpass (PostgreSQL client password file)
    pgpass_path = os.path.join(output_path, ".pgpass")
    with open(pgpass_path, "w") as f:
        f.write("\n".join(pgpass_entries) + "\n")
    os.chmod(pgpass_path, 0o600)  # Set permissions to read/write for the owner only

write_env_file(".env")
write_compose_file("docker-compose.yml")
setup_pgadmin_servers("dockers/services/")
print("Setup completed successfully. Configuration files generated.")
