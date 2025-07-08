Solar Potential + CityDB v5 Sync (Optional)
-------------------------------------------

These steps are intended for developers working on the solar potential analysis pipeline.

#. **Generate .env file for Sunpot**

   Before running the Sunpot service, you need to generate an environment file (``.env``)
   containing required database and folder path settings.

   Run the following command:

   .. code-block:: bash

      # Linux/macOS
      python3 -m dockers.sunpot.generate-env

      # Windows
      python -m dockers.sunpot.generate-env

   This command reads configuration values from two sources:

- ``configs/configs-sunpot.yml``: Contains Sunpot-specific database connection values such as:

   .. code-block:: yaml

      CITYDBV4_DB: citydb
      CITYDBV4_USER: citydb_user
      CITYDBV4_PASSWORD: citydb_password
      CITYDBV4_EPSG: 25832
      CITYDBV4_HOST: citydbv4

- ``configs/config.yml``: Provides shared project structure information such as:

   .. code-block:: yaml

      base:
         name: sonthofen
         base_dir: "data/{name}/"
         base_sunset_dir: "{base_dir}/sunset/"

- ``configs/config-loader.yml`` (shared paths):

      .. code-block:: yaml

         lod2:
               path:
                  lod2: "{loader/path/base}/lod2/"
                  gml: "{loader/path/processed}/lod2/"

   These settings ensure that:

   - **Input geometry data (e.g., LOD2)** is read from the loader-managed directory under ``{loader/path/base}/lod2/``
   - **Solar potential output** is stored under ``base_sunset_dir`` which is ``{base_dir}/sunset/``, keeping it organized per project

#. **Run the Sunpot Service**

   Once the ``.env`` file is in place, start the Sunpot service using:

   .. code-block:: bash

      docker-compose -f ./dockers/sunpot/docker-compose.yml up

   This will launch the solar analysis service using the database connection defined in the ``.env`` file
   and the shared folder structure. The service queries the CityDB v4 instance and performs solar potential
   calculations on the geometry data.

#. **Rebuild if You Modify Source Code**

   If you make changes to Sunpot’s implementation under ``src/services/sunpot/``, you must rebuild the Docker image:

   .. code-block:: bash

      docker-compose -f ./dockers/sunpot/docker-compose.yml up --build

   This ensures that all updates to the code and dependencies are reflected inside the container.

#. **Migrating Solar Potential Calculations to CityDB v5 from CityDB v4**

   Currently, solar potential calculations are only performed using **CityDB v4**.

   Here's how the full workflow is structured:

   1. **LOD2 data ingestion**:
      LOD2 files are downloaded using the `loader` services. You can check them under the ``services/loader/`` directory.
      Since we use bind mounts, once any file is downloaded by a loader, it becomes available in the project's shared base directory.

   2. **Inserting LOD2 data into CityDB v4**:
      The LOD2 files are inserted into the CityDB v4 instance using the Importer/Exporter tool.
      This allows the solar potential calculations to be performed on valid 3D building data.

   3. **Solar potential computation**:
      The Sunpot service runs the analysis and populates the ``sunpot`` schema inside CityDB v4.

   4. **Exporting to CityDB v5**:
      Once the calculations are completed, we run the **export-and-import** step — implemented inside ``src/services/sunpot/``.
      This process:

      - Exports data from CityDB v4 to CSV.
      - Then imports these CSV files into **CityDB v5**
