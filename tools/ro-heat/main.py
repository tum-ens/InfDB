import logging
import numpy as np
import pandas as pd

from src import basic_refurbishment
from src import config, utils, logger
from src.sql import PostgreSQLExecutor

# Parameters
rng = np.random.default_rng(seed=42)
end_of_simulation_year = 2025
construction_year_col = "construction_year"
schema = "ro_heat"


def main():
    try:
        # Initialize logging
        logger.setup_main_logger(None)
        log = logging.getLogger(__name__)

        # Database configuration
        parameters = config.get_db_parameters("citydb")
        # Initialize database executor
        db_executor = PostgreSQLExecutor(
            host=parameters["host"],
            port=parameters["exposed_port"],
            database=parameters["db"],
            username=parameters["user"],
            password=parameters["password"],
        )
        sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"
        db_executor.execute_sql_query(sql)
    
        SQL_QUERY = """
                    DROP TABLE IF EXISTS pylovo_input.temp_rc_calculation;

                    CREATE TABLE pylovo_input.temp_rc_calculation AS
                    WITH wall_data AS (
                        SELECT
                            building_objectid,
                            SUM(area) AS wall_surface_area
                        FROM (
                            SELECT
                                regexp_replace(f.objectid, '_[^_]*-.*$', '') AS building_objectid,
                                CAST(p.val_string AS double precision) AS area
                            FROM feature f
                            JOIN geometry_data gd ON f.id = gd.feature_id
                            JOIN property p ON gd.feature_id = p.feature_id
                            WHERE f.objectclass_id = 709 -- WallSurface
                            AND p.name = 'Flaeche'
                        ) sub
                        GROUP BY building_objectid
                    ),
                    roof_data AS (
                        SELECT
                            building_objectid,
                            SUM(area) AS roof_surface_area
                        FROM (
                            SELECT
                                regexp_replace(f.objectid, '_[^_]*-.*$', '') AS building_objectid,
                                CAST(p.val_string AS double precision) AS area
                            FROM feature f
                            JOIN geometry_data gd ON f.id = gd.feature_id
                            JOIN property p ON gd.feature_id = p.feature_id
                            WHERE f.objectclass_id = 712 -- RoofSurface
                            AND p.name = 'Flaeche'
                        ) sub
                        GROUP BY building_objectid
                    )

                    SELECT
                        b.id AS building_id,
                        b.floor_area,
                        b.floor_number,
                        b.building_type,
                        b.construction_year,
                        -- Reduce wall surface by the assumed window area, see below
                        wd.wall_surface_area - b.floor_area * b.floor_number * 0.75 * 0.2 AS wall_area,
                        rd.roof_surface_area AS roof_area,
                        -- Assume heated area = b.floor_area * b.floor_number * 0.75
                        -- Assume window area to be 0.2 m² per heated area ()
                        b.floor_area * b.floor_number * 0.75 * 0.2 AS window_area
                    FROM pylovo_input.buildings b
                    LEFT JOIN wall_data wd ON b.objectid = wd.building_objectid
                    LEFT JOIN roof_data rd ON b.objectid = rd.building_objectid;

                    SELECT * from pylovo_input.temp_rc_calculation
                    WHERE building_type IS NOT NULL
        """

        engine = config.get_db_engine("citydb")
        with engine.connect() as connection:
            buildings = pd.read_sql(SQL_QUERY, connection)

        log.debug(f"Loaded {len(buildings)} buildings from the database.")
        log.debug(buildings.head())

        random_years = np.full(len(buildings), np.nan)

        # Define class-to-range mapping
        age_class_ranges = {
            "-1919": (1860, 1918),
            "1919-1948": (1919, 1948),
            "1949-1978": (1949, 1978),
            "1979-1990": (1979, 1990),
            "1991-2000": (1991, 2000),
            "2001-2010": (2001, 2010),
            "2011-2019": (2011, 2019),
            "2020-": (2020, end_of_simulation_year),
        }

        # For each class, find matching rows and assign random years
        for age_class, (start, end) in age_class_ranges.items():
            mask = buildings[construction_year_col] == age_class
            count = sum(mask)
            random_years[mask] = rng.integers(start, end, size=count, endpoint=True)

        buildings[construction_year_col] = random_years.astype(int)

        refurbishment_parameters = {
            "outer_wall": {
                "distribution": lambda gen, parameters: gen.normal(**parameters),
                "distribution_parameters": {"loc": 40, "scale": 10},
            },
            "rooftop": {
                "distribution": lambda gen, parameters: gen.normal(**parameters),
                "distribution_parameters": {"loc": 50, "scale": 10},
            },
            "window": {
                "distribution": lambda gen, parameters: gen.normal(**parameters),
                "distribution_parameters": {"loc": 30, "scale": 10},
            },
        }

        refurbed_df = basic_refurbishment.simulate_refurbishment(
            buildings,
            end_of_simulation_year,
            refurbishment_parameters,
            rng,
            age_column=construction_year_col,
            provide_last_refurb_only=True,
        )

        with engine.connect() as connection:
            refurbed_df.to_sql(
                "buildings_rc", connection, if_exists="replace", schema=schema, index=False
            )

        # Run SQL: 01_calculate_r_values
        db_executor.execute_sql_scripts("sql", "01_calculate_r_values.sql")

        log.info("Ro-heat sucessfully completed")

    except Exception as e:
        log.error(f"Something went wrong: {str(e)}")
        raise e


if __name__ == "__main__":
    main()
