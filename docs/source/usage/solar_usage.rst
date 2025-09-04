Solar Potential Calculation
===========================

InfDB includes a solar potential analysis service (Sunpot) that estimates how much sunlight each roof surface receives.  
This is an **optional module**, ideal for users working with LOD2 3D building data.

When the solar pipeline runs:

1. LOD2 geometry is loaded into a temporary **CityDB v4** instance.
2. Sunlight exposure is simulated using predefined parameters.
3. Results are exported and stored in the **CityDB v5** schema for long-term use.

You can enable this module **after the Data Loader setup is complete** and all 3DCityDB services are up and running.

Step 1: Generate the `.env` File for Sunpot
-------------------------------------------

Before launching the solar potential service, generate the required ``.env`` file for Docker Compose:

.. code-block:: bash

    # Linux/macOS
    python3 -m dockers.sunpot.generate-env

    # Windows
    python -m dockers.sunpot.generate-env

This script pulls values from your existing configuration files:

- **Database connection (CityDB v4)** — defined in ``configs/config-sunpot.yml``:

  .. code-block:: yaml

        CITYDBV4_DB: citydb
        CITYDBV4_USER: citydb_user
        CITYDBV4_PASSWORD: citydb_password
        CITYDBV4_EPSG: 25832
        CITYDBV4_HOST: citydbv4

- **Base output directory** — from ``base`` in ``configs/config.yml``:

  .. code-block:: yaml

    base:
      name: sonthofen
      path:
        base: "infdb-data/"
      base_sunset_dir: "{base/path/base}/sunset/"

- **LOD2 input directories** — from ``loader.paths`` in ``configs/config-loader.yml``:

  .. code-block:: yaml

    loader:
      path:
        base: "{base/path/base}/lod2/"
        processed: "{base/path/base}/{base/name}/lod2/"

These values ensure:

- LOD2 input geometry is read from: ``{loader/path/base}`` → e.g., ``infdb-data/lod2/``
- Results are stored in: ``{base/base_sunset_dir}`` → e.g., ``infdb-data/sunset/``


Step 2: Run the Sunpot Service
------------------------------

Once the ``.env`` file is created and CityDB v4 is running, launch the solar service:

.. code-block:: bash

    docker-compose -f ./dockers/sunpot/docker-compose.yml up

This will:

- Connect to **CityDB v4** using the credentials from the ``.env`` file
- Perform **solar potential simulations** on the LOD2 data
- Export and transfer results into the ``sunpot`` schema of CityDB v4

If you are **not running in detached mode**, the terminal output will show the sequential creation of containers:

.. code-block:: text

    ✔ Container sunpot-citydbv4-1                 Created                                  0.4s 
    ✔ Container sunpot-import-to-v4-1             Created                                  0.5s 
    ✔ Container sunpot-sunpot-core-1              Created                                  0.4s 
    ✔ Container sunpot-sunpot-texture-1           Created                                  0.4s 
    ✔ Container solarpotential-export-and-import  Created                                  0.5s 

.. note::

   The **solar pipeline is sequential** — only one service runs at a time (except `citydbv4`, which stays up).  
   Some steps depend on `citydbv4`.

To see real-time status of the Sunpot pipeline, run:

.. code-block:: bash

    watch -n 2 "docker-compose -f ./dockers/sunpot/docker-compose.yml ps"

This refreshes the status table every 2 seconds.

Example snapshot:

.. code-block:: text

    Every 2.0s: docker-compose -f ./dockers/sunpot/docker-compose.yml ps

    NAME                    IMAGE                               COMMAND                  SERVICE        CREATED         STATUS         PORTS
    sunpot-citydbv4-1       3dcitydb/3dcitydb-pg:13-3.2-4.4.0   "docker-entrypoint.s…"   citydbv4       2 minutes ago   Up 2 minutes   0.0.0.0:5435->5432/tcp
    sunpot-import-to-v4-1   3dcitydb/impexp                     "impexp import /data…"   import-to-v4   1 minute ago    Up 10 seconds

.. tip::

   If you modify the Sunpot code in ``src/services/sunpot/``, rebuild the containers using:

   .. code-block:: bash

       docker-compose -f ./dockers/sunpot/docker-compose.yml up --build


Step 3: CityDB v5 Sync Workflow
-------------------------------

By default, results are stored in **CityDB v4**.  
To make them accessible through the unified InfDB API, they must be **migrated to CityDB v5**.

This step is automatic:

1. Ensure **CityDB v5** is running (already done during Data Loader setup)
2. Sunpot will:
   - Export CSV results into: ``{base/base_sunset_dir}``
   - Import those CSVs into the ``sunpot`` schema of **CityDB v5**

.. note::

   This transfer allows downstream services (e.g., solar dashboards or APIs)  
   to query solar results from the same CityDB v5 instance as other geospatial data.
