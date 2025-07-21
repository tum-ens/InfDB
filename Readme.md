# Startup

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
    uv venv --python 3.12
```

## activate environment
```bash
    # linux and macos
    source venv/bin/activate
    # windows
    venv\Scripts\activate
```

## install packages (only once)
```bash
    # install requirements
    uv pip install -r requirements.txt
```

## generate docker compose and env files
You need to generate the configurations files once you changed any of the config yaml files in configs directory.
```bash
    # on linux and macos
    python3 -m src.utils.generate-compose

    # on windows
```

## start infdb
```bash
    # on linux and macos
     docker compose -f docker-compose.yml --env-file .env up --build

    # on windows
```


## load data
```bash
    # on linux and macos
    docker compose -f dockers/loader/loader.yml --env-file .env up --build
    docker compose -f dockers/loader/citydb-tool.yml --env-file .env up --build

    # on windows
```
