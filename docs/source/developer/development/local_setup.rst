Local Development Setup
------------------------

#. **Clone the repository**

   .. code-block:: bash

      git clone https://gitlab.lrz.de/tum-ens/need/infdb.git
      cd infdb

#. **Set up a virtual environment**

   .. code-block:: bash

      python -m venv venv

      # Windows
      venv\Scripts\activate

      # Linux/macOS
      source venv/bin/activate

#. **Install Python dependencies**

   .. code-block:: bash

      pip install -r requirements.txt

#. **Configure Services**

   Configuration files live under the ``configs/`` directory.
   Refer to ``configs/Readme.md`` for documentation on all parameters.

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
         status: active
         path: "{base/path/base}/{base/name}/timescaledb/"

   Services marked with ``status: active`` will be included in the generated
   Docker Compose file and launched at runtime.

#. **Loader Configuration**

   loader-specific settings live in ``configs/config-loader.yml``.
   This file controls dataset sources, directory layout, schemas, and more.

   Example (``configs/config-loader.yml``):

   .. code-block:: yaml

      loader:
         lod2:
            status: active
            url:
            - "https://geodaten.bayern.de/odd/a/lod2/citygml/meta/metalink/09780139.meta4"
            path:
            lod2: "{loader/path/base}/lod2/"
            gml: "{loader/path/processed}/lod2/"


   Base configuration example:

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

      configs:
      - config-loader.yml
      - config-services.yml


   Placeholders like ``{base/path/base}``, ``{services/citydb/user}``, and ``{services/citydb/password}`` are automatically resolved. 
    
   Each project depending on the ``{base/name}``, will be stored under ``infdb-data/{base/name}``.
   As an example, if your project name is ``sonthofen``, you will see the data under ``infdb-data/sonthofen``.

   Each project keeps its own data, including:

   - Raw downloads
   - Unzipped or processed datasets
   - Notebooks or custom files

#. **Supported Modules**

   All modules use ``status: active`` or ``inactive`` to toggle processing.

   - **Zensus 2022** – Census data with 10km grid resolution.
   - **LOD2** – 3D city model in CityGML format.
   - **BKG** – Geodata from the Federal Agency for Cartography.
   - **Basemap** – Map layers in `.gpkg` format.
   - **PLZ** – Postal code geometries in GeoJSON.

   Each module defines its own subdirectories (e.g., ``zip/``, ``unzip/``, ``processed/``),
   making the data flow modular and easier to manage.

#. **Generate Docker Compose File**

   You can generate the `docker-compose.yml` file based on the active service config:

   .. code-block:: bash

      # Linux/macOS
      python3 -m dockers.generate-compose

      # Windows
      python -m dockers.generate-compose

   This script reads ``configs/config-services.yml`` and writes a Compose file that includes
   only services with ``status: active``.

#. **Start Database Services (TimescaleDB + 3DCityDB)**

   Once the compose file is ready, start the services with:

   .. code-block:: bash

      docker-compose -f ./dockers/docker-compose.yml up

   This launches the defined services (TimescaleDB, 3DCityDB, etc.) in the order they appear.

   If loader modules are ``active`` in ``configs/config-loader.yml``, they will automatically
   begin processing and loading data into the running database.

#. **Start the FastAPI application**

   .. code-block:: bash

      fastapi dev src/main.py

#. **(Optional) Rebuild containers after loader code changes**

   .. code-block:: bash

      docker-compose -f ./dockers/docker-compose.yml up --build
