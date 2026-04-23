# Usage

## Requirements Input Data
- LOD2 building data
- Census 2022
- Openmeteo data

## Configuration
The tool can be configured via the configuration file `configs/config-infdb-basedata-buildings.yaml`. An example configuration is shown below:

```yaml title="configs/config-infdb-basedata-buildings.yaml"
infdb-basedata-buildings:
    config-infdb: "config-infdb.yml" # only filename - change path in ".env" file "CONFIG_INFDB_PATH"
    logging:
        path: "infdb-basedata-buildings.log"
        level: "INFO" # ERROR, WARNING, INFO, DEBUG
    hosts:
        postgres:
            user: None
            password: None
            db: None
            host: None
            exposed_port: None
            epsg: None # 3035 (Europe)
    data:
        input_schema: opendata  # (1)
        output_schema: basedata # (2)
        census_building_type_resolution: 1km #1km, 100m # (3)
        random_seed: 0.98   # (4)
```

1. Input Schema - Opendata: Contains preloaded data from Zensus, LOD2, openmeteo that is required for processing basedata-buildings and generating the basedata schema.
2. Output Scehma - Basedata: Contains the post processed buildings-related data from base-data buildings.
3. The original Zensus 2022 data is defined for a 100m by 100m and a 1km by 1km scale. This option allows the user to recalibrate or choose the base-data processing based on either the 100m or 1km scale.  
The **1km scale offers data that is more complete** as less information is hidden due to privacy concerns. The **100m scale could enable better accuracy for processed building information**, provided that only minimal data is obscured or hidden.  
1km scale is more suitable for rural or less densely populated cities, whereas a 100m scale would make more sense for urban/densely populated cities, as less information will be hidden due to privacy concerns.
4. Set a random seed for reproducibility.   
Since some of the functions of base-data buildings involve stochastic assignment of certain variables (e.g. Fill construction year), this seed assignment allows users to reproduce identical results for multiple runs of base-data buildings.

## Run Single AGS
To run the tool for a single AGS, you can use the bash script `tools/tools.sh`:
```bash
bash tools/tools.sh -t infdb-basedata-buildings AGS
```
## Run Multiple AGS
The `run_ags.py` script allows you to run a profile or a single tool for multiple AGS in parallel. The script uses the `uv` to manage the python packages and dependencies.
```bash
# Single Tool
uv run python3 tools/run_ags.py -t infdb-basedata-buildings [-a AGS1,AGS2,... -n NUM_WORKERS -c]
```
More details about the parameters can be found in the [Tools](../index.md) section.
