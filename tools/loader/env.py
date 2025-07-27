from src import config, utils

# This function writes configuration for services into a .env file which then be read by the containers.
def write_env_file(file_path=".env"):
    path = file_path
    # print("Writing environment variables to {}".format(path))
    parameter = utils.get_db_parameters("citydb")

    env_string = f"""CITYDB_HOST={parameter["host"]}
CITYDB_PORT={parameter["exposed_port"]}
CITYDB_NAME={parameter["db"]}
CITYDB_USERNAME={parameter["user"]}
CITYDB_PASSWORD={parameter["password"]}
CITYDB_SRID={parameter["epsg"]}
LOADER_CONFIG_INFDB_PATH={config.get_value(["loader", "path", "config-infdb"])}
LOADER_DATA_PATH={config.get_value(["loader", "path", "base"])}
LOADER_LOD2_PATH={config.get_value(["loader", "sources", "lod2", "path", "gml"])}
    """

    with open(path, "w") as f:
        f.write(env_string)

write_env_file(".env")
print(".env created successfully.")