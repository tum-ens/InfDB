# Startup

## uv install
```bash
    status = config.get_value(["loader", "basemap", "status"])
    citydb_db = config.get_value(["services", "citydb", "db"])
```

## create environment
```bash
    # linux and macos
    source venv/bin/activate
    # windows
    venv\Scripts\activate
    
    # install requirements
    uv pip install -r requirements.txt
```

## generate docker compose and env files
```bash
    # on linux and macos
    python3 -m python3 -m src.utils.generate-compose
    
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
    
    # on windows
```