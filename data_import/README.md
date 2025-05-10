# Import Open Data

## Prequires
- Docker
- Aria2 (Downloader for meta4 files)
```bash
sudo apt install aria2c # Download-Manager LOD2-Data (Building)
```
## Sources
- Buildings (LOD2): GeoPortal Bavaria: https://geodaten.bayern.de/opengeodata/OpenDataDetail.html?pn=lod2&active=MASSENDOWNLOAD
- Streets: Basemap.de: https://basemap.de/open-data/
- Administrative areas (NUTS/VG500): https://gdz.bkg.bund.de/index.php/default/verwaltungsgebiete-1-5-000-000-stand-01-01-vg5000-01-01.html
- PLZ: Zip code areas: https://www.suche-postleitzahl.org/downloads

## Folder Structure

### Config and Source Code
- The folder `configs` in the project root contains the configuration file `config.json`
- The folder `src/imp` contains source code to import the data
- The folder `src/imp/sunpot` contains configs and information to calculate the solar roof potential.

### (Open) Data
- The placeholder `name` is also defined in `config.json`.
- The placeholder `base_dir` - as default `data/` in root project folder - is defined in `config.json`.

The following data folders are at `base_dir/$name/*`:

| Folder   | Description                          |
|----------|--------------------------------------|
| opendata | Storage for all downloaded open data |
| 3dcdb    | Storage for 3D-City-DB Instance      |
| venv     | Virtual python environment           |
| tmp      | Temporary (user) files               |
| backup   | Backup                               |


## Configuration
 The standard configruation is stored in `configs/config.json` file
```json
{
    "general": {
        "name": "sonthofen",
        "base_dir": "data/{name}/",
        "scope": "DE27E"
    },
    "database": {
        "host": "localhost",
        "port": "1235",
        "user": "postgres",
        "password": "need",
        "epsg": "25832",
        "db_dir": "{base_dir}/3dcdb/"
    },
    "opendata": {
        "opendata_dir": "{base_dir}/opendata",
        "zensus_2022": {
            "resolutions": ["100m"],
            "zensus_2022_dir": "{opendata_dir}/zensus_2022/",
            "zensus_2022_zip_dir": "{zensus_2022_dir}/zip/",
            "zensus_2022_unzip_dir": "{zensus_2022_dir}/unzip/",
            "zensus_2022_processed_dir": "{zensus_2022_dir}/processed/",
            "url": "https://www.zensus2022.de/DE/Ergebnisse-des-Zensus/_inhalt.html",
            "schema": "census2022"
        },
        "lod2": {
            "url": ["https://geodaten.bayern.de/odd/a/lod2/citygml/meta/metalink/09780139.meta4"],
            "lod2_dir": "{opendata_dir}/lod2/",
            "gml_dir": "{lod2_dir}/gml/"
        },
        "bkg": {
            "bkg_dir": "{opendata_dir}/bkg/",
            "bkg_zip_dir": "{bkg_dir}/zip/",
            "bkg_unzip_dir": "{bkg_dir}/unzip/",
            "bkg_processed_dir": "{bkg_dir}/processed/",
            "schema": "bkg"
        },
        "basemap": {
            "url": "https://basemap.de/dienste/opendata/basisviews/basisviews_bdlm_BY_EPSG:4326_2025-03-20.gpkg",
            "basemap_dir": "{opendata_dir}/basemap/",
            "basemap_processed_dir": "{basemap_dir}/processed/",
            "schema": "basemap"
        }
    }
}
```

### Services and Ports

| Service                     | Port |
|-----------------------------|------|
| 3D City DB                  | 1235 |
| pgAdmin                     | 81   |
| Jupyter Lab                 | 8888 |

### Startup
From the root project folder you can start the import by executing these commands via bash:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt 

python3 -m src.startup.py
```

File to start import of several data sources `startup.py`
```python
from src import start_infdb
from src.imp import imp_lod2
from src.imp import imp_bkg
from src.imp import imp_census2022
from src.imp import imp_basemap
from src.imp import imp_plz

# Start inf-db
start_infdb.start_infdb()

# Load LOD2 (building data)
imp_lod2.import_lod2()

# Load BKG
imp_bkg.import_bkg()

# Load Census2022
imp_census2022.import_census2022()

# Load Basemap
imp_basemap.import_basemap()

# Load Zip Codes
imp_plz.import_plz()
```