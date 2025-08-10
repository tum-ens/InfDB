Data Loader
===========

InfDB includes a Data Loader that prepares your datasets, sets up the required services (e.g., 3DCityDB, TimescaleDB), and organizes your project files.

When the loader runs:

- Required services (e.g., city model and weather databases) are started automatically
- Configurations are read from internal files in the ``configs/`` directory
- Datasets are downloaded, structured, and stored in consistent project folders
- Once finished, the system is ready to be used via the API or extended modules like solar potential analysis

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
        network_name: network
        environment: container
        base_sunset_dir: "{base/path/base}/sunset/"

    configs:
    - config-loader.yml
    - config-services.yml

- ``name``: Dataset identifier — here, ``sonthofen``.
- ``path/base``: Path that infdb data will be stored under. In this case it will be ``infdb-data``.
- ``base_sunset_dir``: Resolves to ``infdb-data/sunset/``.

These paths control where your data is stored and processed.

Step 2: Enable Required Services
--------------------------------

Edit ``configs/config-services.yml`` if you want to change the current configurations for services:

.. code-block:: yaml

    services:
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


Step 3: Loader-Specific Configuration
-------------------------------------

This step configures the **loader**, which defines:

- What databases to connect to
- Where input and output files are stored
- What data sources are available

Placeholders like ``{name}``, ``{base_dir}``, and ``{loader_dir}`` are automatically resolved  
using values from ``configs/config.yml`` defined in **Step 1**.

.. code-block:: yaml

    loader:
        hosts:
        paths:
        sources:

Loader Hosts
~~~~~~~~~~~~

This section defines database connection details.

.. code-block:: yaml

    hosts:
        citydb:
            user: "{services/citydb/user}"
            password: "{services/citydb/password}"
            db: "{services/citydb/db}"
            host: "{services/citydb/host}"     # Use "localhost" for local development
            port: 5432                          # Use 5433 for exposed port if needed
            epsg: "{services/citydb/epsg}"
        timescaledb:
            user: "{services/timescaledb/user}"
            password: "{services/timescaledb/password}"
            db: "{services/timescaledb/db}"
            host: "{services/timescaledb/host}" # Use "localhost" for local development
            port: 5432

Loader Paths
~~~~~~~~~~~~

Specifies where the loader finds and stores data on the filesystem.

.. code-block:: yaml

    path:
        base: "{base/path/base}/opendata"
        processed: "{base/path/base}/{base/name}"

These values depend on the ``base`` configuration in Step 1. For example:

.. code-block:: yaml

    base:
        name: sonthofen
        path:
            base: "infdb-data/"

This results in:

- ``{base/path/base}`` → ``infdb-data/``
- ``{base/name}`` → ``sonthofen``

So the final paths will be:

- ``base`` → ``infdb-data/opendata``
- ``processed`` → ``infdb-data/sonthofen``

Loader Sources
~~~~~~~~~~~~~~

This section lists all datasets that the loader should handle.  
Example: ``zensus_2022``

.. code-block:: yaml

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

Other defined sources include:

- **Zensus 2022** – 10km statistical grids
- **LOD2** – 3D building models in CityGML
- **BKG** – Official German geodata
- **Basemap** – Raster/vector base maps (.gpkg)
- **PLZ** – Postal code geometries (GeoJSON)

Each of these sources follows the same structure and conventions.

Step 4: Verify Setup
--------------------

#. Confirm Docker is installed and running.
#. You're now ready to launch the services.

.. note::

    You can replicate this setup for any dataset by changing the ``name`` field and adjusting the directory structure accordingly.


Service Initialization
----------------------

#. **Generate Docker Compose and Environment Files**

When you generate the Docker Compose file, InfDB also creates a corresponding ``.env`` file  
that is **used by Docker Compose to inject configuration values** (such as ports, directories, or image tags).

The following files are generated:

- ``dockers/.env``
- ``dockers/docker-compose.yml``

These files are based on your inputs from:

- ``configs/config.yml`` (e.g., project name, base paths)
- ``configs/config-services.yml`` (e.g., which services are active)
  
Generate the Docker Compose file using one of these commands:

.. code-block:: bash

    # Linux/macOS
    python3 -m src.utils.generate-compose

    # Windows
    python -m src.utils.generate-compose

This creates a ``docker-compose.yml`` and ``.env`` file with only the active services.

.. note::

    Do **not edit** the generated ``.env`` or ``docker-compose.yml`` manually.  
    Instead, modify the source configuration files and regenerate as above.

Here is an example of what the generated ``docker-compose.yml`` might look like:

.. code-block:: yaml

    name: infdb
    include:
    - ./loader.yml
    - ./citydb.yml
    - ./timescaledb.yml
    - ./pgadmin.yml
    - ./jupyter.yml
    volumes:
    timescale_data: null
    citydb_data: null
    pgadmin_data: null
    networks:
    network:
        driver: bridge

#. **Start the INFDB Services**

   Launch all active services (TimescaleDB, CityDB, pgAdmin, Jupyter, etc.):

   .. code-block:: bash

       docker-compose -f ./dockers/docker-compose.yml up

   If loader modules are active, datasets will be downloaded and loaded automatically.

   When not running in detached mode (without ``-d``), you should see output similar to:

   .. code-block:: text

       [+] Running 7/7
        ✔ Network infdb_default      Created                                             0.1s 
        ✔ Network infdb_network      Created                                             0.1s 
        ✔ Container infdb-jupyter-1  Created                                             0.3s 
        ✔ Container citydb           Created                                             0.2s 
        ✔ Container timescaledb      Created                                             0.3s 
        ✔ Container loader           Created                                             0.2s 
        ✔ Container pgadmin          Created                                             0.2s 

   If you are using a container management tool like Docker Desktop,  
   you can also check the status of running containers visually.

   Otherwise, use the following command to verify container statuses and ports:

   .. code-block:: bash

       docker-compose -f ./dockers/docker-compose.yml ps

   Example output:

   .. code-block:: text

       NAME              IMAGE                               COMMAND                  SERVICE       CREATED         STATUS                   PORTS
       citydb            3dcitydb/3dcitydb-pg:5.0.0          "docker-entrypoint.s…"   citydb        3 minutes ago   Up 3 minutes (healthy)   0.0.0.0:5433->5432/tcp
       infdb-jupyter-1   jupyter/scipy-notebook:latest       "tini -g -- start-no…"   jupyter       3 minutes ago   Up 3 minutes (healthy)   0.0.0.0:8888->8888/tcp
       loader            infdb-loader                        "python -u -m src.se…"   loader        3 minutes ago   Up 3 minutes             
       pgadmin           dpage/pgadmin4                      "/entrypoint.sh"         pgadmin       3 minutes ago   Up 3 minutes             443/tcp, 0.0.0.0:81->80/tcp
       timescaledb       timescale/timescaledb:latest-pg14   "docker-entrypoint.s…"   timescaledb   3 minutes ago   Up 3 minutes (healthy)   0.0.0.0:5432->5432/tcp

#. **Verify pgAdmin Connection**

   Once `pgadmin` is up, open your browser and go to:

   ::

       http://0.0.0.0:81

   Use the credentials defined in ``configs/config-services.yml`` to log in.  
   You should then see the pgAdmin login page:

   .. image:: ../../img/pg-admin-landing.png
      :alt: pgAdmin Login Screen
      :align: center

   When connecting to the databases, pgAdmin will ask for passwords like this. Again, use the credentials defined in ``configs/config-services.yml`` to log in:

   .. image:: ../../img/pgadmin-db-cred.png
      :alt: Enter database credentials
      :align: center

   After logging in and connecting, you will see something like this:

   .. image:: ../../img/pg-admin-preview.png
      :alt: pgAdmin loaded schemas
      :align: center

#. **Access Jupyter Notebooks**

   Once `jupyter` is running, check the logs for the access token:

   .. code-block:: bash

       docker-compose -f ./dockers/docker-compose.yml logs -f jupyter

   Example log output:

   .. code-block:: text

       jupyter-1  |     To access the server, open this file in a browser:
       jupyter-1  |         file:///home/jovyan/.local/share/jupyter/runtime/jpserver-7-open.html
       jupyter-1  |     Or copy and paste one of these URLs:
       jupyter-1  |         http://668bad70d3e0:8888/lab?token=05688f10b1a7ec0d7ff9a989b4aaff8421663a2494e02da3
       jupyter-1  |         http://127.0.0.1:8888/lab?token=05688f10b1a7ec0d7ff9a989b4aaff8421663a2494e02da3

   Open one of those URLs in your browser and you'll land on:

   .. image:: ../../img/jupyter-auth.png
      :alt: Jupyter token-based login
      :align: center

#. **Start the API Server**

   Launch the FastAPI application using Docker Compose:

   .. code-block:: bash

      docker compose -f dockers/docker-compose.yml --env-file .env up --build

#. **Load Data**

   .. code-block:: bash

      docker compose -f dockers/loader/loader.yml --env-file .env up --build

#. **Process Data**

   .. code-block:: bash

      docker compose -f dockers/processor.yml --env-file .env up --build

#. **Start the API Server**

   Once services are running and data is loaded and processed, launch the FastAPI app:

   .. code-block:: bash

      docker-compose up

   In the background, this runs the following command inside the container:

   .. code-block:: yaml

      CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

   If everything is working correctly, the output should indicate that the server has started:

   .. code-block:: text

      infdb-app  | INFO:     Started server process [1]
      infdb-app  | INFO:     Waiting for application startup.
      infdb-app  | INFO:     Application startup complete.
      infdb-app  | INFO:     Uvicorn running on http://0.0.0.0:8000

   Then you should be able to reach your documentation via:

   .. code-block:: text

      server   Documentation at http://127.0.0.1:8000/docs

   and also for the requests you can use:

   .. code-block:: text

      http://127.0.0.1:8000/

   because we have exposed the app with `8000:8000`.

   Open your browser and either:

   - Visit the Swagger documentation at: ``http://127.0.0.1:8000/docs``
   - Use the shortcut: ``http://localhost:8000/docs``
   - Use your preferred tools (e.g., Postman, curl, or a frontend) to make API requests

   **Swagger landing page:**

   .. image:: ../../img/swagger-local.png
      :alt: Swagger UI main page
      :align: center

   **Example Expanded Swagger Endpoint:**

   This view provides full documentation for the selected API route, including:

   - **Input schema**: required fields, types, formats, and examples
   - **Response types**: data structures for success and error responses
   - **Status codes**: e.g., ``200 OK``, ``400 Bad Request``, ``422 Validation Error``
