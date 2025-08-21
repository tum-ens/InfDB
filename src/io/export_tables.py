import os
import geopandas as gpd
import pandas as pd
import pathlib


def export_time_series_from_pg(
    engine,
    table_name: str,
    export_path: str,
    columns=None,
):
    """
    Export time‑series data from CityDB to CSV or Parquet.

    Args
    ----
    engine      : SQLAlchemy DB connection
    table_name  : Table name in the DB
    export_path : Target file path
    format      : 'csv' | 'parquet'
    columns     : Optional list[str] of columns to include
    """
    col_string = ", ".join(f'"{col}"' for col in columns) if columns else "*"
    query = f"SELECT {col_string} FROM {table_name}"
    df = pd.read_sql(query, engine)

    format = pathlib.Path(export_path).suffix.lower()
    if format == ".csv":
        df.to_csv(export_path, index=False)
    elif format == ".parquet":
        df.to_parquet(export_path, index=False, engine="pyarrow")
    else:
        raise ValueError("Format must be 'csv' or 'parquet'")

    print(f"Time‑series exported as {format.upper()} → {export_path}")


def export_geospatial_from_pg(
    engine,
    table_name: str,
    geom_col: str,
    export_path: str,
    columns=None,
    layer_name: str | None = None,
    mode: str = "w",
):
    """
    Export geospatial data from CityDB to GeoJSON, GeoParquet, or GeoPackage.

    Parameters
    ----------
    engine      : SQLAlchemy engine
    table_name  : Schema‑qualified table name
    geom_col    : Geometry column in the table
    export_path : Target file path ('.geojson', '.parquet', or '.gpkg')
    format      : 'geojson' | 'geoparquet' | 'gpkg' (alias 'geopackage')
    columns     : Optional list[str] excluding geometry (geom always included)
    layer_name  : Optional layer name inside the GPKG (defaults to last
                  part of table_name)
    mode        : 'w' = overwrite (default) • 'a' = append new layer to
                  existing .gpkg
    """

    col_string = ", ".join(f'"{col}"' for col in columns) if columns else "*"
    query = f"SELECT {col_string} FROM {table_name}"
    gdf = gpd.read_postgis(query, engine, geom_col=geom_col)

    format = pathlib.Path(export_path).suffix.lower()
    if format == ".geojson":
        gdf.to_file(export_path, driver="GeoJSON")
    elif format == ".parquet":
        gdf.to_parquet(export_path, index=False)
    elif format == ".gpkg":
        layer = layer_name or table_name.split(".")[-1]
        write_mode = "a" if (mode == "a" and os.path.exists(export_path)) else "w"
        gdf.to_file(
            export_path,
            layer=layer,
            driver="GPKG",
            mode=write_mode,
        )
    else:
        raise ValueError(
            "Format must be 'geojson', 'geoparquet', or 'gpkg'/'geopackage'"
        )

    print(f"Geospatial data exported as {format.upper()} → {export_path}")


# ---------------------------------------------------------------------------
#                               USAGE EXAMPLES
# ---------------------------------------------------------------------------
# engine = utils.get_db_engine("citydb", "localhost")
# export_time_series_from_pg(
#     engine,
#     table_name="opendata.bkg_nuts250_n3",
#     export_path="output1.csv",
#     columns=["NUTS_NAME", "OBJID"],
# )

# export_time_series_from_pg(
#     engine,
#     table_name="opendata.bkg_nuts250_n3",
#     export_path="output11.csv",
# )

# export_time_series_from_pg(
#     engine,
#     table_name="opendata.bkg_nuts250_n3",
#     export_path="output12.parquet",
#     columns=["NUTS_NAME", "OBJID"],
# )

# df = pd.read_parquet("output12.parquet")
# print(df.head())

# export_time_series_from_pg(
#     engine,
#     table_name="opendata.bkg_nuts250_n3",
#     export_path="output13.parquet",
# )

# df = pd.read_parquet("output13.parquet")
# print(df.head())

# export_geospatial_from_pg(
#     engine,
#     table_name="opendata.bkg_nuts250_n3",
#     geom_col="geometry",
#     export_path="output2.geojson",
# )

# export_geospatial_from_pg(
#     engine,
#     table_name="opendata.bkg_nuts250_n3",
#     geom_col="geometry",
#     export_path="./output3.parquet",
# )
# gdf = gpd.read_parquet("output3.parquet")
# print(gdf.head())

# export_geospatial_from_pg(
#     engine,
#     table_name="opendata.bkg_nuts250_n3",
#     geom_col="geometry",
#     export_path="./output4.gpkg",
# )

# export_geospatial_from_pg(
#     engine,
#     table_name="opendata.bkg_nuts250_n3",
#     geom_col="geometry",
#     export_path="output4.gpkg",
#     mode="a",
#     layer_name="municipalities",
# )

# path = "./output4.gpkg"
# for layer in fiona.listlayers(path):
#     print(f"\n--- Layer: {layer} ---")
#     gdf = gpd.read_file(path, layer=layer)
#     print(gdf.head())
