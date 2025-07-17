# Solar Potential + CityDB v5 Sync (Optional)

These steps are intended for developers working on the solar potential analysis pipeline.

---

## 1. Generate `.env` File for Sunpot

Before running the Sunpot service, you need to generate an environment file (`.env`) containing required database and folder path settings.

Run the following command:

```bash
    # Linux/macOS
    python3 -m dockers.sunpot.generate-env
    # Windows
    python -m dockers.sunpot.generate-env
```

This command reads configuration values from the following sources:
- `configs/configs-sunpot.yml`: Contains Sunpot-specific database connection values such as:
    ```yaml
        CITYDBV4_DB: citydb
        CITYDBV4_USER: citydb_user
        CITYDBV4_PASSWORD: citydb_password
        CITYDBV4_EPSG: 25832
        CITYDBV4_HOST: citydbv4
    ```

- `configs/config.yml`: Provides shared project structure information such as:
    ```yaml
        base:
            name: sonthofen
            base_dir: "data/{name}/"
            base_sunset_dir: "{base_dir}/sunset/"
    ```

- `configs/config-loader.yml` (shared paths):
    ```yaml
        lod2:
            path:
                lod2: "{loader/path/base}/lod2/"
                gml: "{loader/path/processed}/lod2/"
    ```

These settings ensure that:
   - **Input geometry data (e.g., LOD2)** is read from the loader-managed directory under `{loader/path/base}/lod2/
   - **Solar potential output** is stored under `base_sunset_dir which is {base_dir}/sunset/, keeping it organized per project

## 2. Run the Sunpot Service

Once the .env file is in place, start the Sunpot service using:

```bash
docker-compose -f ./dockers/sunpot/docker-compose.yml up
```

This launches the solar analysis service using the database connection defined in the .env file
and the shared folder structure. It connects to the CityDB v4 instance and performs solar potential calculations on the geometry data.

## 3. Rebuild If You Modify Source Code

If you make changes to Sunpot’s implementation under `src/services/sunpot/`, you must rebuild the Docker image:

```bash
docker-compose -f ./dockers/sunpot/docker-compose.yml up --build
```

This ensures that all updates to code and dependencies are reflected inside the container.

## 4. Migrating Solar Potential Calculations to CityDB v5 from CityDB v4

Currently, solar potential calculations are only performed using **CityDB v4**.

### Workflow Overview

#### 1. LOD2 Data Ingestion

- LOD2 files are downloaded using the **loader service** (`services/loader/`).
- Because bind mounts are used, once a file is downloaded by the loader, it becomes available in the project’s shared base directory.

#### 2. Insert LOD2 Data into CityDB v4

- The LOD2 files are inserted into the **CityDB v4** instance using the **Importer/Exporter tool**.
- This ensures valid 3D building geometry is available for solar analysis.

#### 3. Solar Potential Computation

- The **Sunpot** service runs the analysis.
- Results are written to the `sunpot` schema inside **CityDB v4**.

#### 4. Export to CityDB v5

- After computations, the **export-and-import** step (in `src/services/sunpot/`) is triggered.
- This step:
  - **Exports** results from **CityDB v4** to CSV files.
  - **Imports** those CSV files into **CityDB v5**.
