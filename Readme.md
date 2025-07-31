# Startup Guide for InfDB
## Prodcution deployment via docker compose
### setup infDB
You need to generate the configurations files once you changed any of the config yaml files in configs directory.
```bash
    # on linux and macos
    docker compose -f dockers/setup/compose.yml up

    # on windows
```

### start infDB
```bash
    # on linux and macos
     docker compose -f compose.yml up -d

    # on windows
```
Hint: If compose.yml is not found, you either forgot to run the command above or something went wrong. 
Please check the logs of the setup service.

### load data
Paths in .env
```yml
CONFIG_INFDB_PATH=../../configs # Path to the configs directory of infDB
LOADER_DATA_PATH=data # Path to data storage
```

Settings in /tools/loader/configs/config-loader.yml

```bash
    # on linux and macos
    docker compose -f tools/loader/compose.yml up 

    # on windows
```

### process data
Paths in .env
```yml
CONFIG_INFDB_PATH=../../configs # Path to the configs directory of infDB
```
Settings in /tools/processor/configs/config-processor.yml
```bash
    # on linux and macos
    docker compose -f tools/processor/compose.yml up 

    # on windows
```

### Remove infDB
```bash
    # on linux and macos
    docker compose -f compose.yml down -v

    # on windows
```

# Configurations (only in addition for QGIS Desktop)
.pg_service.conf for QGIS to connect to InfDB via service
```
[infdb]
host=localhost
port=5432
dbname=citydb
user=citydb_user
password=citydb_password
sslmode=disable
```



## Local development environment for InfDB for developers
### uv install (only once)
```bash
    # on linux and macos by installation script
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # or by pip
    pip install uv
```

### create environment (only once)
```bash
    # linux and macos
    uv sync
```

### activate environment
```bash
    # linux and macos
    source .venv/bin/activate
    # windows
    venv\Scripts\activate
```