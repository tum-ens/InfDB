# Startup Guide for InfDB
## Prodcution deployment via docker compose
### generate docker compose and env files
You need to generate the configurations files once you changed any of the config yaml files in configs directory.
```bash
    # on linux and macos
    docker compose -f dockers/setup/compose.yml up

    # on windows
```

### start infdb
```bash
    # on linux and macos
     docker compose -f .generated/compose.yml --env-file .generated/.env up -d

    # on windows
```

### load data
Settings in /tools/loader/configs/config-loader.yml
```bash
    # on linux and macos
    docker compose -f tools/loader/compose.yml up 

    # on windows
```

### process data
Settings in /tools/processor/configs/config-processor.yml
```bash
    # on linux and macos
    docker compose -f tools/processor/compose.yml up 

    # on windows
```
# Configurations
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