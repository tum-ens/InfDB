Solar Potential Calculation
===========================

InfDB includes a solar potential analysis service that estimates how much sunlight each roof surface receives.

This is an **optional feature** and is useful for users who want to assess solar energy potential using their own 3D building data (LOD2).

When the solar pipeline runs:

1. LOD2 geometry is loaded into a temporary CityDB v4 instance.
2. Sunlight exposure is simulated using predefined parameters.
3. Results are exported and written into a persistent CityDB v5 schema for further use.

You can enable this workflow after the loader setup is complete and 3DCityDB services are running.

#. **Generate .env File for Sunpot**

    Before launching the service, generate the `.env` file that defines database and directory settings.

    .. code-block:: bash

        # Linux/macOS
        python3 -m dockers.sunpot.generate-env

        # Windows
        python -m dockers.sunpot.generate-env

    This script pulls values from two configuration files:

    - ``configs/configs-sunpot.yml`` (database connection):

        .. code-block:: yaml

            CITYDBV4_DB: citydb
            CITYDBV4_USER: citydb_user
            CITYDBV4_PASSWORD: citydb_password
            CITYDBV4_EPSG: 25832
            CITYDBV4_HOST: citydbv4
    
    - ``configs/config.yml``:

        .. code-block:: yaml

            base:
                name: sonthofen
                path:
                    base: "infdb-data/"
                base_sunset_dir: "{base/path/base}/sunset/"

    - ``configs/config-loader.yml`` (shared paths):

        .. code-block:: yaml

            lod2:
                path:
                    lod2: "{loader/path/base}/lod2/"
                    gml: "{loader/path/processed}/lod2/"

    These ensure:

    - Input geometry is read from: ``{loader/path/base}/lod2/``
    - Output results are stored in: ``{base/path/base}/sunset/``

#. **Run the Sunpot Service**

    Once the `.env` file is created and CityDB v4 is running:

    .. code-block:: bash

        docker-compose -f ./dockers/sunpot/docker-compose.yml up

    This will:

    - Connect to CityDB v4 using credentials in the `.env` file
    - Perform solar potential calculations on the loaded LOD2 data
    - Store results in the `sunpot` schema of CityDB v4

#. **Rebuild if You Modify Sunpot Code**

    If you make changes to ``src/services/sunpot/`` or its dependencies:

    .. code-block:: bash

        docker-compose -f ./dockers/sunpot/docker-compose.yml up --build

#. **CityDB v5 Sync Workflow**

    By default, results are written to **CityDB v4**.

    To move the results into **CityDB v5**, the system runs an internal export/import pipeline:

    1. Make sure CityDB v5 is running (via loader setup)
    2. The Sunpot pipeline will:
        - Export results from CityDB v4 into CSVs in ``base_sunset_dir`` which will be resolved as ``infdb-data/sunset/``
        - Import those CSVs into CityDB v5 using the script under ``src/services/sunpot/``
