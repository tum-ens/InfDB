import os

import numpy as np
import pandas as pd
# entise package has to type stubs
from entise.core.generator import Generator  # type: ignore
from infdb import InfDB

from src import refurbishment, tabula_handling, timedata

# Parameters
construction_year_col = "construction_year"


def main():
    # Load InfDB handler
    infdbhandler = InfDB(tool_name="ro-heat", config_path="configs/config-ro-heat.yml")
    ags = infdbhandler.get_env_variable("AGS")

    # Database connection
    infdbclient_citydb = infdbhandler.connect()

    # Logger setup
    infdblog = infdbhandler.get_logger()

    # Start message
    infdblog.info(f"Starting {infdbhandler.get_toolname()} tool")
    infdblog.info("AGS environment variable: %s", ags)

    # Setup database engine
    engine = infdbclient_citydb.get_db_engine()

    # Get configuration values
    input_schema = infdbhandler.get_config_value(["ro-heat", "data", "input", "schema"])
    output_schema = infdbhandler.get_config_value(["ro-heat", "data", "output", "schema"])
    simulation_year = infdbhandler.get_config_value(["ro-heat", "data", "input", "simulation_year"])
    refurbishment_config = infdbhandler.get_config_value(["ro-heat", "data", "refurbishment"])
    method = infdbhandler.get_config_value(["ro-heat", "data", "input", "method"])
    random_seed = infdbhandler.get_config_value(["ro-heat", "data", "input", "random_seed"])
    heating_setpoint = infdbhandler.get_config_value(["ro-heat", "data", "input", "heating_setpoint"])
    heated_area_ratio = infdbhandler.get_config_value(["ro-heat", "data", "input", "Heated_Area_Ratio"])
    rng = np.random.default_rng(seed=random_seed)

    try:
        # Create output schema if it does not exist
        sql = f"CREATE SCHEMA IF NOT EXISTS {output_schema};"
        infdbclient_citydb.execute_query(sql)
        infdblog.info(f"output schema: {output_schema} created successfully")

        # Get building data from database
        full_path = os.path.join("sql", "01_get_building_surface_data.sql")
        format_params = {
            "ags": ags,
            "input_schema": input_schema,
        }
        buildings = infdbclient_citydb.get_pandas_sqlfile(full_path, format_params=format_params)

        if len(buildings) == 0:
            infdblog.warning(f"No buildings found for AGS {ags}. Returning without result")
            return

        infdblog.info(f"Loaded {len(buildings)} buildings from the database.")

        # Sample construction years for buildings
        buildings[construction_year_col] = refurbishment.sample_construction_year(
            buildings, simulation_year, construction_year_col, rng
        )

        # Sample refurbishment status for buildings
        infdblog.info("Starting refurbishment simulation")
        refurbishment_simulation_parameters = {
            n: {
                "distribution": lambda gen, parameters: gen.normal(**parameters),
                "distribution_parameters": {"loc": i["lifespan_mean"], "scale": i["lifespan_spread"]},
            }
            for n, i in refurbishment_config.items()
        }
        refurbed_df = refurbishment.simulate_refurbishment(
            buildings,
            simulation_year,
            refurbishment_simulation_parameters,
            rng,
            age_column=construction_year_col,
        )
        refurbishment_quotas = {n: {"refurbed_fraction": i["quota"]} for n, i in refurbishment_config.items()}
        infdblog.debug("Refurbishment simulation completed")

        # Harmonize refurbishment status with quotas
        infdblog.info("Starting harmonization with refurbishment quotas")
        harmonized_df = refurbishment.harmonize_with_quota(
            refurbed_df,
            refurbishment_quotas,
            rng,
            infdblog,
            age_column=construction_year_col,
        )
        infdblog.debug("Harmonization with refurbishment quotas completed")

        infdblog.info("Writing harmonized refurbishment data to database")
        harmonized_df.to_sql(
            f"temp_buildings_refurbished_status_{ags}", engine, if_exists="replace", schema=output_schema, method="multi",
            index=False,
            index_label="building_objectid",
        )
        format_params_output_schema = {
            "output_schema": output_schema,
            "ags": ags,
            "tool_name": infdbhandler.get_toolname(),
            "process_id": os.getpid(),
        }
        infdbclient_citydb.execute_sql_file(os.path.join("sql", "upsert_buildings_refurbished_status.sql"),
                                            format_params_output_schema)

        # Calculate R & C values by constructing building elements
        infdblog.info("Starting construction of building elements")
        
        full_path = os.path.join("sql", "02_get_tabula_elements.sql")
        tabula_elements = infdbclient_citydb.get_pandas_sqlfile(full_path, format_params=format_params_output_schema)
        infdblog.debug(f"Loaded {len(tabula_elements)} building elements from the database.")
        tabula_structure = tabula_handling.create_tabula_structure(tabula_elements)
        infdblog.debug("Tabula structure created")
        
        harmonized_df[["resistance", "capacitance"]] = harmonized_df.apply(
            lambda row: tabula_handling.calculate_rc_values(tabula_structure, row, heated_area_ratio), axis=1, result_type="expand"
        )
        infdblog.debug("Done with construction of building elements")

        infdblog.info("Writing R & C values")
        rc_values = harmonized_df[["building_objectid", "resistance", "capacitance"]]
        rc_values.to_sql(
            f"temp_buildings_rc_{ags}",
            con=engine,
            if_exists="replace",
            schema=output_schema,
            method="multi",
            index=False,
            index_label="building_objectid",
        )
        infdbclient_citydb.execute_sql_file(os.path.join("sql", "upsert_buildings_rc.sql"), format_params_output_schema)
        infdblog.debug("Done writing R & C values")

        # Start heat demand calculation
        infdblog.info(f"Running heat demand calculation with method {method}")
        start_time = f"{simulation_year}-01-01"
        end_time = f"{simulation_year}-12-31"

        if method == "1R0C_internal":
            format_params = {
                "output_schema": output_schema,
                "ags": ags,
                "start_time": start_time,
                "end_time": end_time,
                "temp_in": heating_setpoint,
                "tool_name": infdbhandler.get_toolname(),
                "process_id": os.getpid(),
            }
            infdbclient_citydb.execute_sql_file(
                os.path.join("sql", "03_heat-demand-r.sql"), format_params=format_params
            )
            infdbclient_citydb.execute_sql_file(os.path.join("sql", "04_debug_demand.sql"), format_params=format_params)

            # Summary
            # # TODO: Adapt output format to EnTiSe format
            # sql = f"CREATE TABLE IF NOT EXISTS {output_schema};"
            # infdbclient_citydb.execute_query(sql)

        elif method == "1R1C" or method == "1R0C":
            bld2ts = timedata.get_bld2ts(database_connection=engine)

            all_ts_df = timedata.get_all_timeseries_data(
                database_connection=engine,
                start=pd.Timestamp(start_time),
                end=pd.Timestamp(end_time),
            )
            all_ts_df.index.name = "datetime"
            all_ts_df.rename(columns={"value": "air_temperature[C]"}, inplace=True)
            data = {x: y.sort_index().reset_index() for x, y in all_ts_df.groupby("ts_metadata_id")}

            # Preparation for EnTiSe
            entise_input = rc_values.reset_index().rename(columns={"building_objectid": "id"})
            entise_input = entise_input.rename(
                columns={"resistance": "resistance[K W-1]", "capacitance": "capacitance[J K-1]"}, errors=True
            )
            entise_input["hvac"] = method
            entise_input["min_temperature[C]"] = heating_setpoint
            entise_input["max_temperature[C]"] = 24.0
            entise_input["init_temperature[C]"] = heating_setpoint
            entise_input["gains_solar"] = 0.0
            entise_input["ventilation[W K-1]"] = 0.0

            entise_input = entise_input.merge(
                bld2ts[["bld_objectid", "ts_metadata_id"]].rename(columns={"ts_metadata_id": "weather"}),
                left_on="id",
                right_on="bld_objectid",
                how="left",
            ).drop(columns=["bld_objectid"])

            # Initialize the generator
            gen = Generator()
            gen.add_objects(entise_input)

            # Generate time series and summary
            summary, dict_df = gen.generate(data, workers=os.cpu_count())

            # Summary
            summary.index.name = "building_objectid"
            summary.to_sql(
                f"temp_entise_summary_{ags}",
                con=engine,
                if_exists="replace",
                schema=output_schema,
                index=True,
                method="multi",
            )
            infdbclient_citydb.execute_sql_file(os.path.join("sql", "upsert_entise_summary.sql"),
                                                format_params_output_schema)

            infdblog.info(summary.head())

            # Time Series
            write_timeseries = False
            if not write_timeseries:
                infdblog.info("Skipping EnTiSe output time series writing to database as per configuration")
                return

            timedata.write_ts_data(dict_df, engine, infdbclient_citydb, infdbhandler, infdblog, output_schema)
        else:
            raise ValueError("Method must be 1R0C or 1R1C")

    except Exception as e:
        infdblog.exception()
        infdbhandler.stop_logger()
        raise e


if __name__ == "__main__":
    main()
