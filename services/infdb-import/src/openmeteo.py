import io
import os
import sys
from typing import Any, Dict

import infdb as InfDB
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

from . import utils

# ============================== Constants ==============================


CACHE_EXPIRE_SECONDS: int = -1  # never expire
RETRY_ATTEMPTS: int = 5
RETRY_BACKOFF: float = 0.2

TS_METADATA_SUFFIX: str = "_ts_metadata"
HOURLY_RESOLUTION_TEXT: str = "1 hour"
HOURLY_UNIT_TEXT: str = "°C"
GEO_SRID_WGS84: int = 4326


def fetch_timeseries(pd_dataframe: pd.DataFrame, engine: Any, infdb: InfDB, variables: list) -> None:
    """Fetches hourly data from Open-Meteo for multiple variables and bulk loads to Postgres.

    Args:
        pd_dataframe: DataFrame with columns ['id', 'latitude', 'longitude'].
        engine: SQLAlchemy Engine connected to the target DB.
        infdb: To extract package configuration object (used for schema/prefix and timing).
        variables: List of variable names to fetch (e.g., ['temperature_2m', 'wind_speed_10m']).
    """
    log = infdb.get_worker_logger()
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession(".cache", expire_after=CACHE_EXPIRE_SECONDS)
    retry_session = retry(cache_session, retries=RETRY_ATTEMPTS, backoff_factor=RETRY_BACKOFF)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Target DB schema/tables
    db_schema = infdb.get_config_value([infdb.get_toolname(), "sources", "openmeteo", "schema"])
    db_prefix = infdb.get_config_value([infdb.get_toolname(), "sources", "openmeteo", "prefix"])
    table_name = "openmeteo_ts_data"

    # Drop & create metadata table
    try:
        with infdb.connect() as db:
            db.execute_query(f"DROP TABLE IF EXISTS {db_schema}.{db_prefix}{TS_METADATA_SUFFIX};")
    except Exception as e:
        log.error("Failed to drop metadata table: %s", e)

    try:
        with infdb.connect() as db:
            db.execute_query(f"""
            CREATE TABLE IF NOT EXISTS {db_schema}.{db_prefix}{TS_METADATA_SUFFIX} (
                id SERIAL PRIMARY KEY,
                name text,
                decription text,
                grid_id text,
                type text,
                resolution text,
                unit text,
                changelog integer,
                group_id text,
                geom geometry,
                UNIQUE(grid_id, name, type)
            );

            CREATE INDEX IF NOT EXISTS {db_prefix}_ts_metadata_id_idx
                ON {db_schema}.{db_prefix}{TS_METADATA_SUFFIX} (id);
            CREATE INDEX IF NOT EXISTS {db_prefix}_ts_metadata_name_idx
                ON {db_schema}.{db_prefix}{TS_METADATA_SUFFIX} (name);
            CREATE INDEX IF NOT EXISTS {db_prefix}_ts_metadata_type_idx
                ON {db_schema}.{db_prefix}{TS_METADATA_SUFFIX} (type);
            CREATE INDEX IF NOT EXISTS {db_prefix}_ts_metadata_resolution_idx
                ON {db_schema}.{db_prefix}{TS_METADATA_SUFFIX} (resolution);
            CREATE INDEX IF NOT EXISTS {db_prefix}_ts_metadata_geom_idx
                ON {db_schema}.{db_prefix}{TS_METADATA_SUFFIX} USING GIST (geom);
            """)
    except Exception as e:
        log.error("Failed to create metadata table: %s", e)

    # Ensure data table exists (TimescaleDB hypertable)
    with infdb.connect() as db:
        db.execute_query(f"DROP TABLE IF EXISTS {db_schema}.{table_name};")

    with infdb.connect() as db:
        db.execute_query(f"""
        CREATE TABLE IF NOT EXISTS {db_schema}.{table_name} (
            ts_metadata_id integer,
            time timestamptz,
            value double precision
        )
        WITH (
            timescaledb.hypertable,
            timescaledb.partition_column='time',
            timescaledb.segmentby='ts_metadata_id'
        );

        CREATE INDEX IF NOT EXISTS {table_name}_ts_metadata_id_time_idx
            ON {db_schema}.{table_name} (ts_metadata_id, time);
        CREATE INDEX IF NOT EXISTS {table_name}_value_idx
            ON {db_schema}.{table_name} (value);
        """)

    log.info("Open-Meteo: processing %d grid locations with variables: %s", len(pd_dataframe), ", ".join(variables))

    # Time window
    start_date = infdb.get_config_value([infdb.get_toolname(), "sources", "openmeteo", "timing", "start_time"])
    end_date = infdb.get_config_value([infdb.get_toolname(), "sources", "openmeteo", "timing", "end_time"])

    # Process in batches of 100 locations (API limit)
    for batch in range(0, len(pd_dataframe), 100):
        batch_df = pd_dataframe.iloc[batch : batch + 100]

        lat_str = ",".join(map(str, batch_df["latitude"].tolist()))
        lon_str = ",".join(map(str, batch_df["longitude"].tolist()))

        # Request all variables in a single API call
        variables_str = ",".join(variables)
        params: Dict[str, str] = {
            "latitude": lat_str,
            "longitude": lon_str,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": variables_str,
        }

        responses = openmeteo.weather_api("https://archive-api.open-meteo.com/v1/archive", params=params)

        # Process multiple locations
        for i, response in enumerate(responses):
            log.debug(
                "Coords: %.6f N, %.6f E | Elev: %.1f m | TZ offset: %ds",
                response.Latitude(),
                response.Longitude(),
                response.Elevation(),
                response.UtcOffsetSeconds(),
            )

            hourly = response.Hourly()
            grid_id = batch_df.iloc[i]["id"]
            longitude = response.Longitude()
            latitude = response.Latitude()

            # Process each variable
            for var_idx, variable_name in enumerate(variables):
                variable_data = hourly.Variables(var_idx).ValuesAsNumpy()

                hourly_data: Dict[str, Any] = {
                    "time": pd.date_range(
                        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                        freq=pd.Timedelta(seconds=hourly.Interval()),
                        inclusive="left",
                    )
                }

                # Determine unit based on variable type
                if "temperature" in variable_name:
                    unit = "°C"
                elif "wind_speed" in variable_name:
                    unit = "m/s"
                elif "precipitation" in variable_name:
                    unit = "mm"
                else:
                    unit = ""

                # Insert metadata record and get the id
                insert_metadata_sql = f"""
                INSERT INTO {db_schema}.{db_prefix}{TS_METADATA_SUFFIX}
                    (name, decription, grid_id, type, resolution, unit, changelog, group_id, geom)
                VALUES
                    ('{db_prefix}_hourly_{variable_name}',
                     '{variable_name.replace("_", " ").title()} from Open-Meteo, hourly',
                     '{grid_id}',
                     'measurement:{variable_name}',
                     '{HOURLY_RESOLUTION_TEXT}',
                     '{unit}',
                     0,
                     'openmeteo',
                     ST_SetSRID(ST_MakePoint({longitude},{latitude}), {GEO_SRID_WGS84}))
                ON CONFLICT (grid_id, name, type) DO UPDATE SET
                    decription = EXCLUDED.decription,
                    resolution = EXCLUDED.resolution,
                    unit = EXCLUDED.unit,
                    geom = EXCLUDED.geom
                RETURNING id;
                """

                ts_metadata_id = None
                try:
                    with engine.begin() as conn:
                        result = pd.read_sql(insert_metadata_sql, con=conn)
                        if not result.empty:
                            ts_metadata_id = int(result["id"].iloc[0])
                            log.debug("Metadata record for %s, grid %s: id=%s", variable_name, grid_id, ts_metadata_id)
                except Exception as e:
                    log.error("Failed to insert/retrieve metadata record for %s: %s", variable_name, e)
                    continue

                # Prepare COPY buffer
                hourly_data["value"] = variable_data
                hourly_data["ts_metadata_id"] = ts_metadata_id
                hourly_dataframe = pd.DataFrame(data=hourly_data)

                conn = None  # ensure defined for the exception path
                try:
                    buf = io.StringIO()
                    hourly_dataframe[["ts_metadata_id", "time", "value"]].to_csv(buf, index=False, header=False)
                    buf.seek(0)

                    conn = engine.raw_connection()
                    cur = conn.cursor()
                    copy_sql = (
                        f"COPY {db_schema}.{table_name} (ts_metadata_id, time, value) FROM STDIN WITH (FORMAT csv)"
                    )
                    cur.copy_expert(copy_sql, buf)
                    conn.commit()
                    cur.close()
                    conn.close()
                    log.debug(
                        "COPYed %d rows for %s (location %d/%d)",
                        len(hourly_dataframe),
                        variable_name,
                        i + 1,
                        len(responses),
                    )
                except Exception as e:
                    try:
                        if conn is not None:
                            conn.rollback()
                            conn.close()
                    except Exception:
                        pass
                    log.error("Failed to COPY hourly data for %s to Postgres: %s", variable_name, e)


def load(infdb: InfDB) -> bool:
    """Prepares grid, queries Open-Meteo, and loads temperature time series.

    Behavior preserved:
    - Early exit (True) when feature flag `openmeteo` is inactive.
    - Creates/ensures 10km BKG grid (delegates to bkg.create_geogitter).
    """
    log = infdb.get_worker_logger()
    try:
        if not utils.if_active("openmeteo", infdb):
            return True
        # Create base directory for Openmeteo data
        base_path = infdb.get_config_path([infdb.get_toolname(), "sources", "openmeteo", "path", "base"], type="loader")
        os.makedirs(base_path, exist_ok=True)

        # DB engine via package
        engine = infdb.get_db_engine()

        # Read centroid geometry and lat/lon of ags in scope from BKG grid table
        ags_list = utils.fetch_scope_ags_from_db(infdb)
        sql = f"""
            SELECT id,
                ST_Y(ST_Transform(ST_Centroid(geom), {GEO_SRID_WGS84})) AS latitude,
                ST_X(ST_Transform(ST_Centroid(geom), {GEO_SRID_WGS84})) AS longitude
            FROM opendata.bkg_vg5000_gem
            WHERE ags IN ({",".join(f"'{s}'" for s in ags_list)})
        """
        pd_dataframe = pd.read_sql(sql=sql, con=engine)
        log.debug("Grid preview:\n%s", pd_dataframe.head())
        log.info("Total grid cells: %d", len(pd_dataframe))

        # Get list of variables to fetch from config
        variables = infdb.get_config_value([infdb.get_toolname(), "sources", "openmeteo", "data"])
        if not variables:
            log.warning("No variables configured in openmeteo.data, defaulting to temperature_2m")
            variables = ["temperature_2m"]

        log.info("Fetching variables: %s", ", ".join(variables))
        fetch_timeseries(pd_dataframe, engine, infdb, variables)

        log.info("Open-Meteo data loaded successfully")
        sys.exit(0)
    except Exception as err:
        log.exception("An error occurred while processing OPENMETEO data: %s", str(err))
        sys.exit(1)
