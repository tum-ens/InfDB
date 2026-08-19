# Get time series data for a given location and time range
#
# Writing EnTiSe output time series to the database now lives in EnTiSe itself
# (entise.io.storage.PostgresTimescaleStorage). ro-heat only injects the
# domain-specific StorageConfig and hands over the engine; see main.py.

import pandas as pd


def get_hourly_temperature_2m(objectid, database_connection, start_time=None, end_time=None):
    query = f"""
        SELECT time, value from opendata.openmeteo_ts_data
        JOIN opendata.openmeteo_ts_metadata
        ON opendata.openmeteo_ts_data.ts_metadata_id = opendata.openmeteo_ts_metadata.id
        JOIN basedata.bld2grid ON opendata.openmeteo_ts_metadata.grid_id = basedata.bld2grid.id
        WHERE objectid='{objectid}' and
            openmeteo_ts_metadata.name='openmeteo_hourly_temperature_2m' and
                time >= '{start_time}'
            AND time <  '{end_time}'
        ORDER BY time ASC;
    """
    df = pd.read_sql(sql=query, con=database_connection)
    df.set_index("time", inplace=True)

    return df


def get_distinct_building_ids(database_connection):
    query = """
            SELECT DISTINCT objectid
            FROM opendata.building_lod2 \
            """
    df = pd.read_sql(sql=query, con=database_connection)
    return df["objectid"].tolist()


def get_all_timeseries_data(database_connection, start, end, ags):
    # Restrict to the weather grids referenced by the AGS's buildings, so a run
    # loads only the series it actually needs rather than every grid in the database.
    query = f"""
        SELECT d.*
        FROM opendata.openmeteo_ts_data d
        WHERE d.time >= '{start}' AND d.time < '{end}'
          AND d.ts_metadata_id IN (
              SELECT DISTINCT bt.ts_metadata_id
              FROM basedata.bld2ts bt
              JOIN basedata.buildings b ON b.objectid = bt.bld_objectid
              WHERE b.gemeindeschluessel LIKE '{ags}'
          )
    """
    df = pd.read_sql(sql=query, con=database_connection)
    df.set_index("time", inplace=True)

    return df


def get_bld2ts(database_connection, ags):
    # Restrict to the AGS's buildings, so the mapping loaded here matches the
    # buildings being processed instead of the full basedata.bld2ts table.
    query = f"""
        SELECT bt.*
        FROM basedata.bld2ts bt
        JOIN basedata.buildings b ON b.objectid = bt.bld_objectid
        WHERE b.gemeindeschluessel LIKE '{ags}'
    """
    df = pd.read_sql(sql=query, con=database_connection)

    return df


def post_timeseries_data(database_connection, df_timeseries):
    df_timeseries.to_sql(
        "openmeteo_ts_data", con=database_connection, schema="opendata", if_exists="append", index=False
    )
