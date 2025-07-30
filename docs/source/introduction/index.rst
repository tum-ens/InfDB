Introduction
============

This site contains comprehensive documentation for users, developers, and administrators of InfDB.

Overview
--------

**InfDB (Infrastructure Database)** is a software platform that combines 3D city models with time-based data like weather or electricity usage. It connects location-based data (such as buildings and streets) with time-related data (such as daily temperatures or energy demand).

InfDB is built on two main technologies:

- **3DCityDB** – to store and manage detailed 3D models of cities.
- **TimescaleDB** – to store time-series data like weather or energy measurements.

This platform helps planners and researchers understand how buildings and infrastructure are affected by changing data over time. It supports better decisions in energy planning and city management.

Goal
----

The ultimate goal of InfDB is to provide a robust foundation for energy system digital twins that can:

1. Support complex energy planning scenarios and "what-if" analyses
2. Enable integration of various data sources (weather, market prices, consumption patterns)
3. Facilitate interoperability with simulation and optimization tools
4. Provide insights for more efficient, resilient, and sustainable energy infrastructure

By combining geospatial capabilities with time-series data management, InfDB aims to be a comprehensive solution for researchers, utilities, and planners working on the future of energy systems.


How It Works
------------

InfDB is built on a modern technology stack:

- **Database Layer**: PostgreSQL with specialized extensions:
  - TimescaleDB for efficient time-series data storage and querying
  - PostGIS for geospatial data handling
  - 3DCityDB for urban modeling

- **API Layer**: FastAPI-based RESTful interface with two main routes:
  - /city - For accessing 3D city model data, including buildings and spatial attributes
  - /weather - For accessing time-series weather data linked to spatial regions

- **Data Model**: Supports comprehensive infrastructure modeling:
  - Energy network components (transformers, substations, power lines)
  - Technical parameters for energy assets
  - Time-series data for various measurements
  - Geospatial relationships between components
