import os
import secrets
import json
from src import config


# This function writes configuration for services into a .env file which then be read by the containers.
def write_env_file(file_path=".env"):
    path = os.path.join(file_path)
    # print("Writing environment variables to {}".format(path))
    with open(path, "w") as f:
        flattened_config = config.flatten_dict(config.get_config(), sep="_")
        for key, value in flattened_config.items():
            env_key = key.upper()
            if "PATH" in env_key:
                if not os.path.isabs(value):
                    # Relative from where the compose file is located here services/*/compose.yml
                    if "SERVICE" in env_key and "COMPOSE_FILE" not in env_key:
                        value = os.path.join("..", "..", value)
                    else:
                        # Relative from where main compase file is located here project root folder
                        value = os.path.join(".", value)
            f.write(f"{env_key}={value}\n")

        # Add JWT secret key for QWC
        f.write("JWT_SECRET_KEY=" + secrets.token_hex(48))
    print(f".env  file written to {path}")


# This function auto generates the docker compose file for us.
def write_compose_file(output_path):
    output = {
        "name": "infdb",
        "include": [],  # loader by default should exist
        "volumes": {"pgadmin_data": None},
        "networks": {
            config.get_value(["base", "network_name"]): {
                "name": config.get_value(["base", "network_name"]),
                "driver": "bridge",
            }
        },
    }

    services = config.get_value(["services"])
    for service_name, props in services.items():
        if isinstance(props, dict) and props.get("status") == "active":
            path = config.get_path(["services", service_name, "path", "compose_file"])
            output["include"].append(path)

    config.write_yaml(output, output_path)
    print(f".docker compose file written to {output_path}")


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
            "PassFile": "/pgadmin4/.pgpass",
        }

        pgpass_entries.append(
            f"{config.get_value(['services', service, 'host'])}:{PORT}:{service}:{config.get_value(['services', service, 'user'])}:{config.get_value(['services', service, 'password'])}"
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
    print(f".pgpass written to {pgpass_path}")


def write_pg_service_conf(output_path):
    """
    Write a pg_service.conf file to enable PostgreSQL connection shortcuts.
    Example usage with psql: `psql service=infdb_citydb`
    """
    services = ["citydb"]  # , "timescaledb"
    port = 5432

    lines = []

    for service in services:
        host = config.get_value(["services", service, "host"])
        db = config.get_value(["services", service, "db"])
        user = config.get_value(["services", service, "user"])
        # password = config.get_value(["services", service, "password"])
        service_name = f"infdb_{service}"

        lines.append(f"[{service_name}]")
        lines.append(f"host={host}")
        lines.append(f"port={port}")
        lines.append(f"dbname={db}")
        lines.append(f"user={user}")
        lines.append("")  # empty line between entries

    # Write file to output path
    pg_service_path = os.path.join(output_path, "pg_service.conf")
    with open(pg_service_path, "w") as f:
        f.write("\n".join(lines))
    print(f"pg_service.conf written to {pg_service_path}")


write_env_file("infdb-root/.env")
write_compose_file("infdb-root/compose.yml")

os.makedirs("infdb-root/.generated/", exist_ok=True)
setup_pgadmin_servers("infdb-root/.generated/")
write_pg_service_conf("infdb-root/.generated/")

print("Setup completed successfully. Configuration files generated.")
