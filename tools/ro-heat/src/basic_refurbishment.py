import pandas as pd
from numpy.random import Generator
from pandas import DataFrame, Series


def simulate_refurbishment(
    df: DataFrame,
    until_year: int,
    parameters: dict,
    random_number_generator: Generator,
    fill_value=0,
    age_column="age",
    provide_last_refurb_only=False,
) -> DataFrame:
    assert (
        age_column in df.columns
    ), f"Column '{age_column}' not in DataFrame, specify the correct column name via the age_column parameter"

    for component, distribution_params in parameters.items():
        distribution = distribution_params["distribution"]
        distribution_params = distribution_params["distribution_parameters"]
        distribution_params["size"] = df.shape[0]

        refurbishment_offsets = DataFrame(index=df.index)
        number_of_refurbishments = 0

        while any(df[age_column] + refurbishment_offsets.sum(axis=1) <= until_year):
            samples = Series(
                index=df.index,
                name=f"{component}_{number_of_refurbishments}",
                # Sample from the distribution using the provided parameters
                data=distribution(random_number_generator, distribution_params)
                .round()
                .astype(int),
            )
            refurbishment_offsets = pd.concat([refurbishment_offsets, samples], axis=1)
            number_of_refurbishments += 1

        refurb_cum_sum = refurbishment_offsets.cumsum(axis=1).astype(int)
        # Calculate the years when the refurb happens by adding the offsets rolling sum to the building age
        refurb_years = refurb_cum_sum.add(df[age_column], axis=0)
        # Mask any refurb_year that is larger than until_year with a fill_value
        refurb_years_masked = refurb_years.mask(refurb_years > until_year, fill_value)
        # Drop rows with all zeros
        zero_columns = refurb_years_masked.columns[
            (refurb_years_masked.T == fill_value).all(axis=1)
        ]
        refurb_years_masked = refurb_years_masked.drop(columns=zero_columns)

        if provide_last_refurb_only:
            # Replace fill_values with building age, so that the last refurb corresponds to the building age if there
            # was no refurb at all
            refurb_years_masked = refurb_years_masked.mask(
                refurb_years_masked == fill_value, df[age_column], axis=0
            )
            df[component] = refurb_years_masked.max(axis=1)
        else:
            df = pd.concat([df, refurb_years_masked], axis=1)

    return df
