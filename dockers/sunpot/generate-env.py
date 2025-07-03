import yaml
import os
from src.core.config import get_value
import subprocess


base_dir = os.path.dirname(__file__)
input_path = os.path.join(base_dir, "../../configs/config-sunpot.yml")
file_path = os.path.join(base_dir, ".env")


def generate_env(config):
    with open(file_path, "w") as f:
        # Write all UPPERCASE top-level keys
        for key, value in config.items():
            if key.isupper():
                f.write(f"{key}={value}\n")

        # Write loader dir
        gml_dir = get_value(["loader", "lod2", "gml_dir"])
        f.write(f"GML_DIR={gml_dir}\n")

        # Write sunset dir
        sunset_dir = get_value(["base", "base_sunset_dir"])
        f.write(f"SUNSET_DIR={sunset_dir}\n")


def docker_login(config):
    registry = "gitlab.lrz.de:5005"
    username = config.get("USERNAME")
    password = config.get("PASSWORD")

    if not username or not password:
        raise RuntimeError("Missing USERNAME or PASSWORD environment variable.")

    result = subprocess.run(
        ["docker", "login", registry, "-u", username, "--password-stdin"],
        input=password.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if result.returncode != 0:
        print(result.stderr.decode())
        raise RuntimeError(
            "Docker login failed.\n"
            "Please check your credentials in 'configs/config-sunpot.yml'.\n"
            "Sunpot will not work unless Docker login is successful."
        )
    else:
        print("Docker login successful")

if __name__ == "__main__":
    with open(input_path, "r") as f:
        config = yaml.safe_load(f)

    docker_login(config)
    generate_env(config)