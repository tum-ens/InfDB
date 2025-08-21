import os

import numpy as np
import pandas as pd
from sqlalchemy import create_engine

from src import basic_refurbishment

host = os.environ["host"]
database = os.environ["database"]
port = os.environ["port"]
user = os.environ["user"]
password = os.environ["password"]

rng = np.random.default_rng(seed=42)
end_of_simulation_year = 2025

engine = create_engine(
    f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
)


construction_year_col = "construction_year"

sql_file = "create_rc_temp_table.sql"

with open(f"./sql/{sql_file}", "r", encoding="utf-8") as file:
    sql_content = file.read()


with engine.connect() as connection:
    buildings = pd.read_sql(sql_content, connection)

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
        "buildings_rc", connection, if_exists="replace", schema="pylovo_input"
    )
