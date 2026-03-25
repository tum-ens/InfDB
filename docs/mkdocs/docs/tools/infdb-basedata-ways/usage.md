# Usage

## Requirements Input Data
- Basemap verkehrslinie
- Opendata buildings

## Configuration
The tool can be configured via the configuration file `configs/config-infdb-basedata-ways.yaml`. An example configuration is shown below:

```yaml title="configs/config-infdb-basedata-ways.yaml"
infdb-basedata-ways:
    config-infdb: "config-infdb.yml" 
    logging:
        path: "infdb-basedata-ways.log"
        level: "INFO" 
    hosts:
        postgres:
            user: None
            password: None
            db: None
            host: None
            exposed_port: None
            epsg: 3035
    data:
        input_schema: opendata
        output_schema: basedata
        use_address_information: true
        klasse_filter:
            - "Wirtschaftsweg"
            - "Hauptwirtschaftsweg"
            - "Gemeindestraße"
            - "Landesstraße, Staatsstraße"
            - "Bundesstraße"
            - "Bundesautobahn"
            - "Kreisstraße"
        klasse_objektart_filter:
            "Bundesstraße":
                - "Strassenachse"
                - "Fahrbahnachse"   
            "Bundesautobahn":
                - "Strassenachse"
        apply_length_filter: True
        min_length_meter: 10
        apply_loop_filter: True
        apply_isolated_filter: True
```

### Configuration parameters

- `input_schema`: Name of the database schema from which the input data is read.
- `output_schema`: Name of the database schema to which the output tables are written.
- `use_address_information`: Boolean flag that enables the use of buildings address information during processing.
- `klasse_filter`: List of allowed `klasse` values that are kept in the input road network.
- `klasse_objektart_filter`: Mapping from `klasse` to a list of allowed `objektart` values. This allows more specific filtering for selected road classes.
- `apply_length_filter`: Boolean flag that enables filtering of segments shorter than the configured minimum length.
- `min_length_meter`: Minimum segment length in meters. Segments shorter than this value are removed when `apply_length_filter` is enabled.
- `apply_loop_filter`: Boolean flag that enables filtering of loop geometries.
- `apply_isolated_filter`: Boolean flag that enables filtering of isolated road segments that are not connected to the main network.

## Run Single AGS
To run the tool for a single AGS, you can use the bash script `tools/tools.sh`:
```bash
bash tools/tools.sh -t infdb-basedata-ways AGS
```
## Run Multiple AGS
The `run_ags.py` script allows you to run a profile or a single tool for multiple AGS in parallel. The script uses the `uv` to manage the python packages and dependencies.
```bash
# Single Tool
uv run python3 tools/run_ags.py -t infdb-basedata-ways [-a AGS1,AGS2,... -n NUM_WORKERS -c]
```
More details about the parameters can be found in the [Tools](../index.md) section.
