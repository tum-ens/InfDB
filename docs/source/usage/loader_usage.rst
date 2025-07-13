Data Loader
===========

InfDB includes a Data Loader that prepares your datasets, sets up the required services (e.g., 3DCityDB, TimescaleDB), and organizes your project files.

When the loader runs:

- Required services are launched (e.g., 3DCityDB, TimescaleDB)
- Datasets are downloaded and structured
- Results are stored in organized folders based on your project name
- The system becomes ready for further analysis (e.g., solar potential, API access)

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

#. **Install Dependencies**

   .. code-block:: bash

      pip install -r requirements.txt

#. **Configure Services**

   Configuration files are under the ``configs/`` directory.  
   These include database access and project structure.

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

      timescaledb:
        user: timescale_user
        password: secret
        db: timescaledb_db
        host: timescaledb
        exposed_port: 5432
        path: "{base/path/base}/{base/name}/timescaledb/"
        status: active

#. **Define Your Project Setup**

   Project-level configuration lives in ``configs/config.yml``.  
   It controls the name and base path of your project.

   Example (``config.yml``):

   .. code-block:: yaml

      base:
        name: sonthofen
        path:
          base: "infdb-data/"
        scope: DE27E
        schema: general
        base_sunset_dir: "{base/path/base}/sunset/"

   Data will be stored under ``infdb-data/sonthofen/`` based on the ``base.name`` setting.

#. **Configure the Loader**

   Loader settings live in ``configs/config-loader.yml``.  
   This includes:

   - Database access (uses the service config)
   - Input/output paths
   - List of datasets to download and process

   Example:

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

#. **Enable or Disable Datasets**

   In ``config-loader.yml``, each dataset has a ``status`` field.  
   Set it to ``active`` to include it during loading.

   Example (partial):

   .. code-block:: yaml

      sources:
        zensus_2022:
          status: active
          resolutions: [10km, 1km]
          path:
            base: "{loader/path/base}/zensus_2022/"
            processed: "{loader/path/processed}/zensus_2022/"

   Supported datasets:

   - **Zensus 2022**
   - **LOD2** – CityGML models
   - **BKG** – Administrative geodata
   - **Basemap** – Raster/vector layers
   - **PLZ** – Postal code boundaries

#. **Generate Docker Compose File**

   .. code-block:: bash

      # Linux/macOS
      python3 -m dockers.generate-compose

      # Windows
      python -m dockers.generate-compose

   This creates a `docker-compose.yml` with only the active services.

#. **Start the Database Services**

   .. code-block:: bash

      docker-compose -f ./dockers/docker-compose.yml up

   Active loader modules will automatically run and process data into the databases.

#. **Start the API Server**

   Once services are running and data is loaded, launch the FastAPI app:

   .. code-block:: bash

      fastapi dev src/main.py
