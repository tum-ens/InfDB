# Local Development Setup

## Requirements

Before setup, ensure the following tools are installed:

- Python 3.12+
- Git ([https://git-scm.com/](https://git-scm.com/))
- Docker and Docker Compose
- *(Optional)* QGIS — useful for geospatial visualization
- UV Package Manager

---

### 1. Install UV Package Manager

```bash
# On Linux and macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
# By pip
pip install uv
```

### 2. Clone the Repository

```bash
git clone https://gitlab.lrz.de/tum-ens/need/infdb.git
cd infdb
```

### 3. Setup a Virtual Environment

```bash
# Create virtual environment
uv venv --python 3.12

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 4. Install Python Dependencies

```bash
# install requirements
uv pip install -r requirements.txt
```

### 5. Configure Services

Configuration files are located in the configs/ directory.
See configs/Readme.md for a description of all available options.

Example (configs/config-services.yml):

```yaml
citydb:
  user: citydb_user
  password: citydb_password
  db: citydb
  host: citydb
  exposed_port: 5433
  epsg: 25832
  path: "{base/path/base}/{base/name}/citydb/"
  status: active

timescaledb:
  user: timescale_user
  password: secret
  db: timescaledb_db
  host: timescaledb
  exposed_port: 5432
  path: "{base/path/base}/{base/name}/timescaledb/"
  status: active
```

Services with status: active will be included in the generated Docker Compose file and launched at runtime.

### 6. Loader-Specific Configuration

Loader configuration is defined in configs/config-loader.yml.
It controls what datasets are loaded, where they are stored, and which schemas they use.

#### 6.1 Define Database Connections
```yaml
hosts:
  citydb:
    user: "{services/citydb/user}"
    password: "{services/citydb/password}"
    db: "{services/citydb/db}"
    host: "{services/citydb/host}"
    port: 5432
    epsg: "{services/citydb/epsg}"

  timescaledb:
    user: "{services/timescaledb/user}"
    password: "{services/timescaledb/password}"
    db: "{services/timescaledb/db}"
    host: "{services/timescaledb/host}"
    port: 5432
```

#### 6.2 Configure Local Paths
```yaml
path:
  base: "{base/path/base}/opendata"
  processed: "{base/path/base}/{base/name}"
These values are pulled from configs/config.yml:
```

```yaml
base:
  name: sonthofen
  path:
    base: "infdb-data/"
  base_sunset_dir: "{base/path/base}/sunset/"
```

This results in:

- `{base/path/base}` → `infdb-data/`
- `{base/name}` → `sonthofen`

**Final paths:**

- `base` → `infdb-data/opendata`
- `processed` → `infdb-data/sonthofen`

#### 6.3 Register Data Sources
Example configuration for the zensus_2022 dataset:

``` yaml
sources:
  zensus_2022:
    status: active
    resolutions:
      - 10km
      - 1km
      - 100m
    path:
      base: "{loader/path/base}/zensus_2022/"
      zip: "{loader/sources/zensus_2022/path/base}/zip/"
      unzip: "{loader/sources/zensus_2022/path/base}/unzip/"
      processed: "{loader/path/processed}/zensus_2022/"
    url: "https://www.zensus2022.de/DE/Ergebnisse-des-Zensus/_inhalt.html"
    schema: opendata
    prefix: cns22
    layer:
      - Zensus2022_Bevoelkerungszahl-Gitter.csv
      - Zensus2022_Anteil_unter_18-Gitter.csv
      - ...
    
```

**Other supported datasets:**

- **LOD2** – 3D city model (CityGML)
- **BKG** – Administrative and statistical boundaries
- **Basemap** – Vector/raster base map layers
- **PLZ** – Postal code zones in GeoJSON

Each dataset uses modular subdirectories and a consistent folder structure.
#### 6.4 Enable or Disable Modules
Each data source can be toggled using status: active or inactive.

### 7. Generate Docker Compose File

```bash
    # On Linux/macOS
    python3 -m src.utils.generate-compose

    # On Windows (if python3 doesn't work)
    python -m src.utils.generate-compose
```

This reads config-services.yml and writes a docker-compose.yml
for only the active services.

### 8. Start Database Services (TimescaleDB + 3DCityDB)
```bash
    docker-compose -f docker-compose.yml --env-file .env up --build
```

### 9. Load data
```bash
    docker compose -f dockers/loader/loader.yml --env-file .env up --build

```
## 10. process data
```bash
    docker compose -f dockers/processor.yml --env-file .env up --build
```

### 11. Start the FastAPI Application
```bash 
fastapi dev src/main.py
```
