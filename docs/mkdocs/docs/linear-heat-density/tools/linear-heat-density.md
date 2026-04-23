---
icon: material/chart-timeline-variant
---
# linear-heat-density :material-chart-timeline-variant:

The **linear-heat-density** tool calculates the linear heat density for street segments by aggregating the heat demand of associated buildings and dividing it by street length. This metric is essential for evaluating the feasibility of district heating networks and is widely used in municipal heat planning and BEW-funded feasibility studies.

---

## Workflow Overview

The workflow consists of **two main steps**:

### 1. Buildings-to-Street Assignment

This step spatially assigns buildings to the nearest street segments to allow aggregation of building heat demands per street segment. 

**Configuration**

The configuration can be done via the configuration YAML file.

```yaml
data:
    streets:
        schema: process_streets
        table: segments
        id-column: id
        geom-column: geom
    buildings:
        schema: basedata
        table: buildings
        id-column: '"objectid"'
        geom-column: geom
    output:
        schema: buildings_to_street
        table: buildings_to_streets
```



* `streets.schema`: Name of the database schema containing street data
* `streets.table`: Table containing street data
* `streets.id-column`: Column with unique street segment identifiers
* `streets.geom-column`: Column with geometry information on the street segments (lines)
* `buildings.schema`: Schema containing building data
* `buildings.table`: Table with building data
* `buildings.id-column`: Column with unique building identifiers
* `buildings.geom-column`: Geometry column of buildings (point or polygon)
* `output.schema`: Schema to store the resulting buildings-to-streets mapping table
* `output.table`: Name of the resulting mapping table linking buildings to street segments


---

### 2. Linear Heat Density Calculation

This step aggregates building heat demand per street segment and divides it by segment length to compute linear heat density.

**Configuration**

The configuration can be done via the configuration YAML file.
```yaml
data:
    input:
        buildings-to-streets:
            schema: buildings_to_street
            table: buildings_to_streets
        streets:
            schema: process_streets
            table: segments
            id-column: id
            geom-column: geom
        heat-demand:
            schema: ro_heat
            table: buildings
            id-column: '"building_objectid"'
            heat-demand-column: '"heating:demand[Wh]"'
    output:
        schema: linear_heat_density
        table: linear_heat_density
```


* `buildings-to-streets.schema`: Schema containing the mapping table from Step 1
* `buildings-to-streets.table`: Mapping table linking buildings to street segments
* `streets.schema`: Schema containing street geometries 
* `streets.table`: Table with street segments
* `streets.id-column`: Unique identifier for each street segment which have to match the IDs in the building-to-streets mapping table 
* `streets.geom-column`: Column containing the street geometries (lines)
* `heat-demand.schema`: Schema containing building heat demand data
* `heat-demand.table`: Table with building-level heat demand
* `heat-demand.id-column`: The building IDs have to match the IDs of the building-to-streets mapping table
* `heat-demand.heat-demand-column`: Column containing annual heat demand of buildings
* `output.schema`: Schema to store the resulting linear heat density table
* `output.table`: Name of the output table containing linear heat density per street segment



!!! note "Under Development"
    This documentation section is currently being expanded.

    **Maintainer**: Caro 