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

        git clone https://gitlab.lrz.de/tum-ens/need/database.git
        cd database

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

        timescaledb:
          user: postgres
          password: password
          db: timescaledb
          host: 127.0.0.1
          port: 5432
          status: active

        citydb:
          user: postgres
          password: password
          db: citydb
          host: 127.0.0.1
          port: 5433
          status: active

#. **Loader Configuration**

    Project-level settings live in ``configs/config.yml``.

    .. code-block:: yaml

        base:
          name: sonthofen
          base_dir: "data/{name}/"
          base_sunset_dir: "{base_dir}/sunset/"

    Loader-specific settings live in ``configs/config-loader.yml``.

    .. code-block:: yaml

        loader:
          loader_dir: "{base_dir}/opendata"

          zensus_2022:
            status: active
            resolutions: [10km]
            zensus_2022_dir: "{loader_dir}/zensus_2022/"
            schema: census2022

    Placeholders like ``{name}``, ``{base_dir}``, and ``{loader_dir}`` are automatically resolved. 
    Files are stored under ``data/{name}/``, which keeps each project isolated and well-structured.

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
        python3 -m dockers.loader.generate-compose

        # Windows
        python -m dockers.loader.generate-compose

#. **Start Database Services**

    Run the following to start all active services (TimescaleDB, CityDB, etc.):

    .. code-block:: bash

        docker-compose -f ./dockers/loader/docker-compose.yml up

    If loader modules are active, they will automatically download and load datasets into the appropriate databases.

#. **Start the API Server**

    Launch the FastAPI application to interact with the data:

    .. code-block:: bash

        fastapi dev src/main.py

