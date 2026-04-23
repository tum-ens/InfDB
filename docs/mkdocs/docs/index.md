# Welcome to InfDB :simple-rocket:

<p align="center">
  <img src="assets/img/logo_infdb.png" alt="InfDB logo" width="100"/>
</p>

**InfDB - Infrastructure and Energy Database** provides a modular and easy-to-configure open-source data and tool infrastructure. It is equipped with essential services, designed to minimize the effort required for data management. We follow a platform-independent containerized approach that streamlines collaboration in energy modeling and analysis, empowering the growth of an ecosystem by offering standardized interfaces and APIs, and by allowing users to dedicate their focus to generating insights rather than handling data logistics.


## Key Features

: :material-plus-circle: **Geospatial, Time Series & Graph Data Support**: PostGIS, TimescaleDB and pgRouting.
: :material-plus-circle: **Platform Independent**: Containerized with Docker.
: :material-plus-circle: **Modular**: extensible via standardized APIs.
: :material-plus-circle: **Open Data**: Automatized import of common opendata sources.
: :material-plus-circle: **FAIR Data**: Focus on providing Findable, Accessible, Interoperable, and Reusable Data.
: :material-plus-circle: **Open Source**: Apache License Version 2.0.

## Why use it?

InfDB addresses common challenges in energy system planning and research, particularly those related to data management. By providing a standardized and modular infrastructure, InfDB reduces the time and effort required to set up and maintain data systems. This allows researchers and planners to focus on their core tasks of modeling and analysis, rather than being bogged down by data logistics.

The InfDB can be used effectively wherever geospatial and time series information is required. Possible applications include:

-   Infrastructure planning such as municipal heat or grid planning activities
-   Research on energy system optimization on energy transition scenarios
-   Geospatial analysis of supply and demand potentials

## Architecture

The architecture of InfDB as shown in figure below is composed of two main components:

: :fontawesome-solid-gears: **[Services](usage/services.md)** – Dockerized core functionalities.
: :material-tools: **[Tools](tools/index.md)** – Dockerized software and tools for specific use cases and data processing tasks.

![InfDB Overview](assets/img/infdb-overview.png)


## Getting Started

Check out the **[Usage Guide](usage/index.md)** to install, configure and run your instance.

## Demo
The **[Linear Heat Density](linear-heat-density/index.md)** use case demonstrates the capabilities of InfDB in the context of municipal heat planning (KWP). 
![](linear-heat-density/liz-browser.png)

## Contribution

Check out the **[Developer Guide](development/index.md)** to learn how to contribute.

## Feedback and contributions

The content of this documentation is brand new! If you encounter a mistake, notice missing content, or have any other input, please get in touch on [GitHub discussions](https://github.com/InfDB/InfDB/discussions), or submit an issue.