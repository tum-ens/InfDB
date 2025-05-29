# Import Open Data

## Prequires
- Docker
- Citydb-tool
```bash
ENV CITYDB_VERSION=1.0.0
ENV CITYDB_TOOL_DIR=/opt/citydb-tool
RUN wget https://github.com/3dcitydb/citydb-tool/releases/download/v1.0.0/citydb-tool-1.0.0.zip && \
    unzip citydb-tool-1.0.0.zip -d /opt && \
    rm citydb-tool-1.0.0.zip && \
    mv /opt/citydb-tool-1.0.0 /opt/citydb-tool

ENV PATH="$PATH:/opt/citydb-tool"
```

- Aria2 (Downloader for meta4 files)
```bash
sudo apt install aria2c # Download-Manager LOD2-Data (Building)
```

## Sources
- Buildings (LOD2): GeoPortal Bavaria: https://geodaten.bayern.de/opengeodata/OpenDataDetail.html?pn=lod2&active=MASSENDOWNLOAD
- Streets: Basemap.de: https://basemap.de/open-data/
- Administrative areas (NUTS/VG500): https://gdz.bkg.bund.de/index.php/default/verwaltungsgebiete-1-5-000-000-stand-01-01-vg5000-01-01.html
- PLZ: Zip code areas: https://www.suche-postleitzahl.org/downloads

### Source Code
- The folder contains source code to import the data

### (Open) Data
- The placeholder `name` is also defined in `config_services.yaml`.
- The placeholder `base_dir` - as default `data/` in root project folder - is defined in `config_services.yaml`.

The following data folders are at `base_dir/$name/*`:

| Folder   | Description                          |
|----------|--------------------------------------|
| opendata | Storage for all downloaded open data |
| venv     | Virtual python environment           |


## Configuration
 The standard configruation for the services is stored in `configs/config_services.yaml` file.
 The configuration for loader sources is stored in `configs.config_loader.yaml` file.

### Services and Ports
| Service                     | Port |
|-----------------------------|------|
| 3D City DB                  | 5433 |
| pgAdmin                     | 81   |
| jupyter                     | 8888 |

These are exposed values. You can check under dockers/<service_name>.yaml files to see what is exposed port for that service.
You can also update them there depending on your needs.
Yaml files read the values `.env` file in the same path which is auto-generated via `config_services`.yaml.

### Startup
From the root project folder you can start the import by executing these commands via bash:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_loader.txt 

python3 -m src.services.loader.startup
```


