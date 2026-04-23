from typing import Any, Dict

import numpy as np
from numpy.random import Generator
from pandas import DataFrame


def sample_construction_year(
    buildings: DataFrame,
    end_of_simulation_year: int,
    construction_year_col: str,
    random_number_generator: Generator,
):
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
        random_years[mask] = random_number_generator.integers(start, end, size=count, endpoint=True)

    return random_years.astype(int)


def simulate_refurbishment(
    df: DataFrame,
    until_year: int,
    parameters: Dict[str, Dict[str, Any]],
    random_number_generator: Generator,
    fill_value: int = 0,
    age_column: str = "age",
) -> DataFrame:
    """
    Simulate component refurbishments by drawing inter-refurbishment intervals from
    user-provided distributions until the given cutoff year.

    parameters format (per component):
      {
        "distribution": callable(gen, params_dict) -> np.ndarray,
        "distribution_parameters": { ... }  # without 'size'; added automatically
      }
    """
    assert age_column in df.columns, (
        f"Column '{age_column}' not in DataFrame, specify the correct column name via the age_column parameter"
    )

    for component, cfg in parameters.items():
        distribution = cfg.get("distribution")
        if distribution is None:
            raise ValueError(f"Missing distribution for component '{component}'.")
        dist_params = dict(cfg["distribution_parameters"])
        dist_params["size"] = df.shape[0]

        refurbishment_offsets = DataFrame(index=df.index)
        n_refurbs = 0

        # Keep sampling while at least one object is still <= until_year
        while any(df[age_column] + refurbishment_offsets.sum(axis=1) <= until_year):
            refurbishment_offsets[f"{component}_{n_refurbs}"] = (
                distribution(random_number_generator, dist_params).round().astype(int)
            )
            n_refurbs += 1

        refurb_cum_sum = refurbishment_offsets.cumsum(axis=1).astype(int)
        refurb_years = refurb_cum_sum.add(df[age_column], axis=0)
        refurb_years_masked = refurb_years.mask(refurb_years > until_year, fill_value)

        # Drop columns that are all fill_value
        zero_cols = refurb_years_masked.columns[(refurb_years_masked.T == fill_value).all(axis=1)]
        refurb_years_masked = refurb_years_masked.drop(columns=zero_cols)

        # If never refurbished, take the original construction year
        refurb_years_masked = refurb_years_masked.mask(refurb_years_masked == fill_value, df[age_column], axis=0)
        df[component] = refurb_years_masked.max(axis=1)

    return df


def harmonize_with_quota(
    df: DataFrame,
    parameters: Dict[str, Dict[str, Any]],
    random_number_generator: Generator,
    logger,
    age_column: str = "age",
) -> DataFrame:
    """
    Enforce that at most target_fraction of buildings are refurbished
    by reverting excess refurbishments to construction year.
    """
    assert age_column in df.columns, (
        f"Column '{age_column}' not in DataFrame, specify the correct column name via the age_column parameter"
    )

    for component, cfg in parameters.items():
        # If no refurbed_building_percentage is provided, all buildings will be refurbished
        refurbed_building_percentage = cfg.get("refurbed_fraction", 1)

        n_refurbishment_target = round(refurbed_building_percentage * df.shape[0])
        # Some buildings might not have been refurbished as they are too young, i.e., their components end of life was
        # not reached. We exclude those from the percentage calculation.
        actually_refurbished_buildings = df[df[component] != df[age_column]]
        n_actually_refurbed = actually_refurbished_buildings.shape[0]

        n_to_keep = min(n_refurbishment_target, n_actually_refurbed)
        n_to_drop = n_actually_refurbed - n_to_keep

        logger.info(
            f"Harmonizing refurbishment simulation with quotes for component {component}: "
            f"target={n_refurbishment_target}, actually={n_actually_refurbed}, to_drop={n_to_drop}"
        )
        if n_refurbishment_target > n_actually_refurbed:
            logger.warning(f"Refurbishment quota for component {component} cannot be met; keeping all refurbishments.")
        # Sample n_to_drop indices to drop from the actually_refurbished_buildings
        idx_to_drop = actually_refurbished_buildings.sample(n_to_drop, random_state=random_number_generator).index
        # Drop the refurbishment by setting the components age to the building age
        df.loc[idx_to_drop, component] = df.loc[idx_to_drop, age_column]

    return df
