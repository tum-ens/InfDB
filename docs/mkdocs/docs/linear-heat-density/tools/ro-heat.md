---
icon: material/radiator
---
# ro-heat :material-radiator:

The **ro-heat** tool is used to estimate the residential building heat demand on a building level. It uses statistical data and building characteristics to estimate the heat demand for each building in the dataset using a single-zone resistance–capacitance model (RC model).

!!! note "Under Development"
    This documentation section is currently being expanded. The tool is fully functional, but detailed documentation is pending.

    **Maintainer**: Martin

**Data Sources Used**

- [3D building models LoD2 Germany (LoD2-DE)](https://gdz.bkg.bund.de/index.php/default/3d-gebaudemodelle-lod2-deutschland-lod2-de.html) by the [Federal Agency for Cartography and Geodesy Germany (B0KG)](https://www.bkg.bund.de/)
- [Census of Germany 2022 (Zensus 2022)](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_inhalt.html)
- TABULA residential building archetypes
- Weather data

## Key Features

- **Extraction of building components**: Building components (external walls, roofs and ground floors) are extracted 
- **Refurbishment simulation**: For each component refurbishment is simulated stochastically by sampling refurbishment intervals from a normal distribution parametrised by component-specific mean lifespans and standard deviations
- **Assignment of building archetypes**: Based on the refurbishment status, each building component is assigned a TABULA archetype that specifies the used materials and their thermal properties
- **Parameter estimation**: Based on the used materials, we estimate the required parameters for the RC model, e.g., resistance and capacitance, per component and aggregate it per building
- **Demand estimation**: Lastly, the parameters are input into [EnTiSe](https://github.com/tum-ens/EnTiSe) with corresponding weather data and temperature set points to estimate heating and cooling demand 



## Output Data

The output datasets are stored in the `ro_heat` schema (the output schema specified in the configuration) of the infDB PostgreSQL database. The main tables created are:

- `buildings_refurbished_status`: Contains detailed building information with attributes such as type, construction year, number of floors, component areas and component refurbishment status.
- `buildings_rc`: Contains parameters for the RC model per building.
- `entise_summary`: Contains heating and cooling demand and load summaries per building.

- 

# Configuration 
The configuration of the tool can be done via the configuration YAML file:
```bash title="configs/config-ro-heat.yml"
ro-heat:
    config-infdb: "config-infdb.yml" # only filename - change path in ".env" file "CONFIG_INFDB_PATH"
    logging:
        path: "ro-heat.log"
        level: "INFO" # ERROR, WARNING, INFO, DEBUG
    hosts:
        postgres:
            user: None
            password: None
            db: None
            host: None
            exposed_port: None
            epsg: None
    data:
        input:
            schema: basedata # (1)
            simulation_year: 2023 # (2)
            heating_setpoint: 20.0 # (3)
            random_seed: 42 # (4) 
            method: 1R1C # (5)
        refurbishment:
            outer_wall: # (6)
                quota: 0.33 # (7)
                lifespan_mean: 40 # (8)
                lifespan_spread: 10 # (9)
            rooftop:
                quota: 0.63
                lifespan_mean: 50
                lifespan_spread: 10
            window:
                quota: 0.9
                lifespan_mean: 30
                lifespan_spread: 10
        output:
            schema: ro_heat # (10)
```

1. Specify the schema where the input data comes from.
2. Specify the simulation year, ensure weather data is available for this year.
3. Specify the heating setpoint in °C, this is input in EnTiSe as `min_temperature[C]` and `init_temperature[C]`.
4. Specify the random seed for the refurbishment simulation for reproducibility.
5. Specify the demand estimation, this is input in EnTiSe as `method`.
6. Specify refurbishment parameters per component, e.g., for outer walls.
7. Specify refurbishment quota for outer walls, e.g., 0.33 means that a third of outer walls will be refurbished at the end of their lifespan.
8. Specify the mean lifespan for outer walls in years. Refurbishment intervals are sampled from a normal distribution parametrised by mean lifespan and spread.
9. Specify the spread of the lifespan for outer walls in years.
10. Specify the schema where the data should be stored.