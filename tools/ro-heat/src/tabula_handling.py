from typing import Any, cast

import numpy as np
from pandas import DataFrame, Series

from . import eureca_code


def create_tabula_structure(tabula_rows: DataFrame) -> DataFrame:
    def _as_str(value: Any) -> str:
        return cast(str, value)

    def _as_float(value: Any) -> float:
        return float(value)

    # Explicitly sort by layer_index according to EUReCA specification
    # EUReCA requires Materials sorted from outside (highest layer_index) to inside (lowest layer_index)
    tabula_rows = tabula_rows.sort_values('layer_index', ascending=False)

    materials = [
        eureca_code.Material(
            _as_str(row.material_name),
            _as_float(row.thickness),
            _as_float(row.thermal_conduc),
            _as_float(row.heat_capac),
            _as_float(row.density),
        )
        for row in tabula_rows.itertuples(index=False)
    ]
    tabula_rows["materials"] = Series(materials, index=tabula_rows.index, dtype="object")

    constructions = (
        tabula_rows.groupby(["building_type", "element_name", "construction_data", "start_year", "end_year"])[
            "materials"
        ]
        .apply(list)
        .reset_index()
    )

    # Map tabula to EUReCA names
    tabula_eureca_element_name_mapping = {
        "GroundFloor": "GroundFloor",
        "OuterWall": "ExtWall",
        "Rooftop": "Roof",
        "Ceiling": "IntCeiling",
        "Floor": "IntFloor",
        "InnerWall": "IntWall",
        "Window": "Window",
    }

    # Create a EUReCA Constructions from the list of materials and assign the correct EUReCA type
    construction_objects = [
        eureca_code.Construction(
            name=f"B{row.construction_data}_{row.element_name}_{row.start_year}_{row.end_year}",
            materials_list=cast(list[Any], row.materials),
            construction_type=tabula_eureca_element_name_mapping[_as_str(row.element_name)],
        )
        for row in constructions.itertuples(index=False)
    ]

    # Extract construction R and C values
    constructions["R"] = Series(
        [obj.thermal_resistance for obj in construction_objects],
        index=constructions.index,
    )
    constructions["C"] = Series(
        [obj.k_int for obj in construction_objects],
        index=constructions.index,
    )
    constructions["C"] = constructions["C"].fillna(0.0)

    return constructions


def calculate_rc_values(tabula: DataFrame, row: Series, area_ratio: float =1.0) -> tuple[float, float]:
    overall_r = 0.0
    overall_c = 0.0
    components = tabula["element_name"].unique()
    for component in components:
        component_tabula = tabula[tabula.element_name == component]
        match = resolve_construction(component_tabula, component, row)

        if component in ["Ceiling", "Floor"]:
            area = row["floor_area"] * max(row["floor_number"] - 1, 1)
        elif component == "InnerWall":
            area = row["floor_area"] * max(row["floor_number"] - 1, 1) * 2.5
        elif component == "Rooftop":
            area = row["roof_area"]
        elif component == "OuterWall":
            area = row["wall_area"]
        elif component == "Window":
            area = row["window_area"]
        elif component == "GroundFloor":
            area = row["floor_area"]
        else:
            raise Exception(f"Unknown component: {component}")

        # Only "OuterWall","GroundFloor", "Rooftop","Window" contribute to R value
        if component in ["OuterWall", "GroundFloor", "Rooftop", "Window"]:
            overall_r = overall_r + (area * area_ratio / match["R"])
        overall_c = overall_c + (match["C"] * area * area_ratio)

    return 1 / overall_r, overall_c


def resolve_construction(tabula: DataFrame, component: str, row: Series) -> Series:
    # Get the corresponding refurbishment year
    # 'GroundFloor', 'Ceiling', 'Floor', 'InnerWall' are not refurbished, therefore,  refurb_year = construction_year
    if component in ["GroundFloor", "Ceiling", "Floor", "InnerWall"]:
        refurb_year = row["construction_year"]
    elif component == "Rooftop":
        refurb_year = row["rooftop"]
    elif component == "OuterWall":
        refurb_year = row["outer_wall"]
    elif component == "Window":
        refurb_year = row["window"]
    else:
        raise ValueError(f"Unknown construction type: {component}")

    # 'Ceiling', 'Floor', 'InnerWall' are not building type specific and have no refurbishment options
    if component in ["Ceiling", "Floor", "InnerWall"]:
        building_type = "standard"
        construction_string = "tabula_de_standard"
    # For all other components check if refurb_year == construction year and build the corresponding string
    else:
        building_type = row["building_type"]
        if refurb_year == row["construction_year"]:
            construction_string = f"tabula_de_standard_1_{building_type}"
        else:
            construction_string = f"tabula_de_retrofit_1_{building_type}"

    candidates = tabula[(tabula.building_type == building_type) & (tabula.construction_data == construction_string)]

    if candidates.empty:
        raise ValueError(f"No TABULA construction found for row: {row}")

    # Check for direct match, i.e., refurb year in TABULA interval
    match = candidates[(candidates.start_year <= refurb_year) & (candidates.end_year >= refurb_year)]

    # If there's no direct match, fall back to closest
    if match.empty:
        dist = np.where(
            refurb_year < candidates.start_year.to_numpy(),
            candidates.start_year.to_numpy() - refurb_year,
            refurb_year - candidates.end_year.to_numpy(),
        )

        # argmin = index of closest range
        i = np.lexsort((candidates.start_year.to_numpy(), dist))[0]
        match = candidates.iloc[i]
    else:
        # Convert DataFrame to Series for equal return types
        match = match.iloc[0]

    return match
