# Compute heat

## Prequires
- Docker
- Have database set up with Open Data (see `src/services/loader`)

## Configuration
Paths in .env
```yml
CONFIG_INFDB_PATH=../../configs # Path to the configs directory of infDB
```
Settings in configs/config-ro-heat.yml
```bash
    # on linux and macos
    docker compose -f tools/ro-heat/compose.yml up 

    # on windows
```

## Calculcate RC and heat
From the root project folder you can start the processor by executing these commands via bash:
```bash
docker compose -f compose.yml up
```

## Source Code
- The folder contains source code to create three tables in the `pylovo_input`:
    - `src`: Contains the source code.
    - `sql`: Contains SQL scripts.
    - `main.py`: Entry point for running the ro-heat.
