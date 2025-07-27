# Startup

### Local development environment for InfDB for developers
## uv install (only once)
```bash
    # on linux and macos
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # by pip
    pip install uv
```

## create environment (only once)
```bash
    # linux and macos
    uv sync
```

## activate environment
```bash
    # linux and macos
    source .venv/bin/activate
    # windows
    venv\Scripts\activate
```

## install packages (only once)
```bash
    # install requirements
    # uv pip install .
```

### Prodcution Deployment via docker compose
## generate docker compose and env files
You need to generate the configurations files once you changed any of the config yaml files in configs directory.
```bash
    # on linux and macos
    docker compose -f dockers/setup/compose.yml up

    # on windows
```

## start infdb
```bash
    # on linux and macos
     docker compose -f .generated/compose.yml --env-file .generated/.env up -d

    # on windows
```

## load data
```bash
    # on linux and macos
    docker compose -f tools/loader/compose.yml --env-file .generated/.env up 

    # on windows
```

## process data
```bash
    # on linux and macos
    docker compose -f tools/processor/compose.yml --env-file .generated/.env up 

    # on windows
```
