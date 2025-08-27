# Compute heat

## Prequires
- Docker
- Have database set up with Open Data

## Configuration
The configuration can be done via [configs/config-ro-heat.yml](configs/config-ro-heat.yml)
```yaml
ro-heat:
    config-infdb: "config-infdb.yml" # only filename - change path in ".env" file "CONFIG_INFDB_PATH"
    logging:
        path: "ro-heat.log"
        level: "INFO" # ERROR, WARNING, INFO, DEBUG
    hosts:
        citydb:
            user: None
            password: None
            db: None
            host: None
            exposed_port: None
            epsg: None # 3035 (Europe)
        timescaledb:
            user: None
            password: None
            db: None
            host: None
            exposed_port: None
    data:
        input_schema: opendata
        output_schema: pylovo_input
```
**Hint:** In case you move the infdb-loader source folder outside of the folder tools in repo or want to change the location where the downloaded data is stored, the paths to data and to configs folder need to be defined in [.env](.env)
```bash
    CONFIG_INFDB_PATH=../infdb/configs  # Change if you moved the "configs" folder
```

Once you adjusted the configuration files with the command above, you need to finally start the infDB-loader and start importing:

## Calculcate RC and heat
From the root project folder you can start the processor by executing these commands via bash:
```bash
    # on linux and macos
    docker compose -f tools/ro-heat/compose.yml up 

    # on windows
```

## Source Code
- The folder contains source code to create three tables in the `pylovo_input`:
    - `src`: Contains the source code.
    - `sql`: Contains SQL scripts.
    - `main.py`: Entry point for running the ro-heat.
