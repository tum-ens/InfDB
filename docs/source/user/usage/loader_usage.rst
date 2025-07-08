Data Loader
===========

InfDB includes a Data Loader that sets up the necessary services (like 3DCityDB and TimescaleDB), manages project structure, and prepares your datasets for use.

When the loader runs:

- Required services (e.g., city model and weather databases) are started automatically
- Configurations are read from internal files in the ``configs/`` directory
- Datasets are downloaded, structured, and stored in consistent project folders
- Once finished, the system is ready to be used via the API or extended modules like solar potential analysis

**Supported Datasets:**

- Building models (LOD2)
- Street networks
- Administrative boundaries
- Postal code regions

Each dataset is stored in its own subfolder (e.g., `zip/`, `unzip/`, `processed/`), and organized automatically.

#. **Clone the Repository**

    .. code-block:: bash

        git clone https://gitlab.lrz.de/tum-ens/need/infdb.git
        cd infdb

#. **Set Up a Virtual Environment**

    .. code-block:: bash

        python -m venv venv

        # Windows
        venv\Scripts\activate

        # Linux/macOS
        source venv/bin/activate

#. **Install Python Dependencies**

    .. code-block:: bash

        pip install -r requirements.txt

#. **Configure Services**

    All configurations live under the ``configs/`` directory.  
    You must be familiar with this folder — especially with the ``base_dir`` setting under ``config.yml``.  
    It controls where your data is stored and processed.

    Example (``configs/config-services.yml``):

    .. code-block:: yaml

        citydb:
            user: citydb_user
            password: citydb_password
            db: citydb
            host: citydb
            exposed_port: 5433
            epsg: 25832
            path: "{base/path/base}/{base/name}/citydb/"
            status: active

#. **Loader Configuration**

    Project-level settings live in ``configs/config.yml``.

    .. code-block:: yaml

        base:
            name: sonthofen
            path:
                base: "infdb-data/"
            scope: DE27E
            schema: general
            network_name: network
            environment: container
            base_sunset_dir: "{base/path/base}/sunset/"

    Loader-specific settings live in ``configs/config-loader.yml``.

    .. code-block:: yaml

        loader:
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
            path:
                base: "{base/path/base}/opendata"
                processed: "{base/path/base}/{base/name}"

    Placeholders like ``{base/path/base}``, ``{services/citydb/user}``, and ``{services/citydb/password}`` are automatically resolved. 
    
    Each project depending on the ``{base/name}``, will be stored under ``infdb-data/{base/name}``.
    As an example, if your project name is ``sonthofen``, you will see the data under ``infdb-data/sonthofen``.

#. **Supported Modules**

    You can activate/deactivate each dataset by setting ``status: active`` or ``status: inactive``.

    - **Zensus 2022** – 10km statistical grids
    - **LOD2** – 3D building models in CityGML
    - **BKG** – Official German geodata
    - **Basemap** – Raster/vector base maps (.gpkg)
    - **PLZ** – Postal code geometries (GeoJSON)

#. **Generate Docker Compose File**

    This step generates the Compose file based on your configs:

    .. code-block:: bash

        # Linux/macOS
        python3 -m dockers.generate-compose

        # Windows
        python -m dockers.generate-compose

#. **Start Database Services**

    Run the following to start all active services (TimescaleDB, CityDB, etc.):

    .. code-block:: bash

        docker-compose -f ./dockers/docker-compose.yml up

    If loader modules are active, they will automatically download and load datasets into the appropriate databases.

#. **Start the API Server**

    Launch the FastAPI application to interact with the data:

    .. code-block:: bash

        fastapi dev src/main.py

