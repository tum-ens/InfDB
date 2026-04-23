# pylovo-generation

The `pylovo-generation` tool creates synthetic low-voltage grid data based on the infdb-basedata.

# Data Sources

Mainly builds upon the following open data sources:

- [Census of Germany 2022 (Zensus 2022)](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_inhalt.html)
- [Official geogrids](https://gdz.bkg.bund.de/index.php/default/geographische-gitter-fur-deutschland-in-utm-projektion-geogitter-national.html) by the [Federal Agency for Cartography and Geodesy Germany (BKG)](https://www.bkg.bund.de/)
- [3D building models LoD2 Germany (LoD2-DE)](https://gdz.bkg.bund.de/index.php/default/3d-gebaudemodelle-lod2-deutschland-lod2-de.html) by the [Federal Agency for Cartography and Geodesy Germany (BKG)](https://www.bkg.bund.de/)
- [Basemap official data](https://basemap.de/) by all surveying authorities of the federal states and the [Federal Agency for Cartography and Geodesy Germany (BKG)](https://www.bkg.bund.de/)

# Features
## Method

- Synthetic low-voltage grids with transformers and radial multi-feeder structure
- Greenfield and brownfield transformer placement with different clustering methods
- Dimensioning with coincidence factors on building, feeder and transformer level to replicate grid planner dimensioning heuristics.

## Tool

- Availability: Based on available open data only
- Geospatial Processing: Utilizes PostgreSQL databases with PostGIS with prebuilt graph algorithms for efficient geodata processing
- Power System Integration: Provides grid models in the format of existing simulation frameworks (pandapower (default), OpenDSS)
- Adoption: Integrated into infdb ecosystem for seamless tool integration

## Usage

If you want to run the tool, first run the [basedata](infdb-basedata.md) and afterward execute:
```bash
bash tools/pylovo-generation/run.sh
```

### Configuration 

The available regions selection is taken from the imported regions listed in the scope table from opendata.
Detailed generation configurations can be adjusted under 'tools/pylovo-generation/configs/config-pylovo-generation.yml'.

### Output Data

The main output of the tool is:

- Grid models for simulation (pandapower/OpenDSS)
- Grid geometries for visualization
- Grid metrics for analysis

The output datasets are stored in the `pylovo` schema of the InfDB PostgreSQL database. The most important tables  are:

- version: Tracks a dataset version incl. comment, creation timestamp, and serialized parameters used for a run.
- equipment_data: Versioned catalog of electrical equipment (e.g. transformers/cables) with technical parameters and costs.
- grid_result: Core output per generated grid/cluster (identified by version_id, kcid, bcid, plz) incl. transformer selection, model status, and the full grid serialized as JSON.
- ways_result: Versioned ways linestrings for a given plz
- buildings_result: Per-building results (geometry, category/type, load, households, connection info) linked to a specific grid and version.
- lines_result: Line geometry and attributes per generated grid  incl. endpoints, type, and length.
- plz_parameters: Aggregated per-postcode JSON summaries (e.g. transformer count, cable length, load/bus counts, distance stats) per (version_id, plz).
- clustering_parameters: Derived characteristic grid metrics per grid for further analysis.
- transformer_positions: Greenfield & Brownfield transformer position per grid with optional OSM reference.

## Further information

- For more detailed information, please refer to the [pylovo documentation](https://pylovo.readthedocs.io/en/main/)
- If you use the pylovo-generation tool in a scientific publication, please cite the following publication:
Reveron Baecker et al. (2025), [Generation of low-voltage synthetic grid data for energy system modeling with the pylovo tool](https://doi.org/10.1016/j.segan.2024.101617)
