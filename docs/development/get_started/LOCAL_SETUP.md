# Local Development Setup

## Requirements

Before setup, ensure the following tools are installed:

- Python 3.10+
- Git ([https://git-scm.com/](https://git-scm.com/))
- Docker and Docker Compose
- *(Optional)* QGIS — useful for geospatial visualization

---

### 1. Clone the Repository

```bash
    git clone https://gitlab.lrz.de/tum-ens/need/infdb.git
    cd infdb
```
### 2. Setup a Virtual Environment

```bash
    python -m venv venv

    # Windows
    venv\Scripts\activate

    # Linux/macOS
    source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
    pip install -r requirements.txt
```

### 4. Configure Services

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

### 5. Loader-Specific Configuration

Loader configuration is defined in configs/config-loader.yml.
It controls what datasets are loaded, where they are stored, and which schemas they use.

#### 5.1 Define Database Connections
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

#### 5.2 Configure Local Paths
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

#### 5.3 Register Data Sources
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
#### 5.4 Enable or Disable Modules
Each data source can be toggled using status: active or inactive.

### 6. Generate Docker Compose File

```bash
    # On Linux/macOS
    python3 -m dockers.generate-compose

    # On Windows (if python3 doesn't work)
    python -m dockers.generate-compose
```

This reads config-services.yml and writes a docker-compose.yml
for only the active services.

### 7. Start Database Services (TimescaleDB + 3DCityDB)
```bash
    docker-compose -f ./dockers/docker-compose.yml up
```


### 8. Start the FastAPI Application
```bash 
fastapi dev src/main.py
```

### 9. (Optional) Rebuild Containers After Loader Code Changes
```bash
    docker-compose -f ./dockers/docker-compose.yml up --build
```
