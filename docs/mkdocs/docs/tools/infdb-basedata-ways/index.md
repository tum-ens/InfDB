# InfDB-basedata-ways
The `basedata-ways` tool processes raw street network data to generate a structured dataset of way segments with associated attributes. The tool performs data cleaning, topology correction, segment generation, and attribute enrichment. The processing is executed through Python-based orchestration and SQL-based transformation steps within InfDB.

## Usage
Details on how to use the tool can be found in the [Usage](usage.md) section.

## Architecture
The architecture of the `infDB-basedata-ways` tool is based on the InfDB Dev Container template as described in the [Tools Template](../dev-container/index.md) section. The tool is implemented in Python and utilizes the `pyinfdb` package for interaction with infDB. The database operations are executed using SQL queries. More details can be found in the [Architecture](architecture.md) section.

## Data Pipeline
More details can be found in the [Data Pipeline](data-pipeline.md) section.

## Tool Overview
- Loads way segments from the Basemap Verkehrslinie dataset for the selected AGS
- Filters the input way network to keep only the classes defined in the configuration
- Assigns buildings to way segments using building address information where available; if no address-based assignment is possible, buildings are assigned to the nearest way segment
- Merges consecutive way segments that belong to the same straight way section and are not separated by a junction, reducing unnecessary segmentation in the network
- Filters way segments based on the configured rules for loops, short segments, and isolated segments
- Splits way segments at intersections so that the way network has a consistent segmented topology
- Creates connection lines between buildings and their assigned way segments
- Creates network nodes from junction points
- Outputs the processed way network for downstream tools

