Local Development Setup
------------------------

#. **Clone the repository**

   .. code-block:: bash

      git clone https://gitlab.lrz.de/tum-ens/need/database.git
      cd database

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

   Services marked with ``status: active`` will be included in the generated
   Docker Compose file and launched at runtime.

#. **Loader Configuration**

   loader-specific settings live in ``configs/config-loader.yml``.
   This file controls dataset sources, directory layout, schemas, and more.

   Base configuration example:

   .. code-block:: yaml

      base:
         name: sonthofen
         base_dir: "data/{name}/"
         scope: DE27E
         schema: general
         network_name: network
         environment: container
         base_sunset_dir: "{base_dir}/sunset/"

   Placeholders like ``{name}``, ``{base_dir}``, and ``{base_sunset_dir}`` will be
   automatically replaced at runtime. For example:

   - ``base_dir`` becomes ``data/sonthofen/``
   - ``base_sunset_dir`` becomes ``data/sonthofen/sunset/``

   Each project keeps its own data in ``data/{name}/``, including:

   - Raw downloads
   - Unzipped or processed datasets
   - Notebooks or custom files

   Sample loader module configuration:

   .. code-block:: yaml

      loader:
      loader_dir: "{base_dir}/opendata"

      zensus_2022:
         status: active
         resolutions:
            - 10km
         zensus_2022_dir: "{loader_dir}/zensus_2022/"
         zensus_2022_zip_dir: "{zensus_2022_dir}/zip/"
         zensus_2022_unzip_dir: "{zensus_2022_dir}/unzip/"
         zensus_2022_processed_dir: "{zensus_2022_dir}/processed/"
         url: "https://www.zensus2022.de/DE/Ergebnisse-des-Zensus/_inhalt.html"
         schema: census2022

   Placeholders like ``{loader_dir}`` and ``{zensus_2022_dir}`` are derived from the base config and expanded automatically.

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
      python3 -m dockers.loader.generate-compose

      # Windows
      python -m dockers.loader.generate-compose

   This script reads ``configs/config-services.yml`` and writes a Compose file that includes
   only services with ``status: active``.

#. **Start Database Services (TimescaleDB + 3DCityDB)**

   Once the compose file is ready, start the services with:

   .. code-block:: bash

      docker-compose -f ./dockers/loader/docker-compose.yml up

   This launches the defined services (TimescaleDB, 3DCityDB, etc.) in the order they appear.

   If loader modules are ``active`` in ``configs/config-loader.yml``, they will automatically
   begin processing and loading data into the running database.

   All downloads, processed files, and outputs are stored under ``data/{name}/``,
   as structured by the configuration and placeholder logic.


#. **Start the FastAPI application**

   .. code-block:: bash

      fastapi dev src/main.py

#. **(Optional) Rebuild containers after loader code changes**

   .. code-block:: bash

      docker-compose -f ./dockers/loader/docker-compose.yml up --build
