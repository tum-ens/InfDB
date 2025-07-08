
.. figure:: docs/img/logo_TUM.png
    :width: 200px
    :target: https://gitlab.lrz.de/tum-ens/super-repo
    :alt: Repo logo

==========
InfDB - Infrastructure and Energy Digital Twin Database
==========



**A comprehensive database system for creating digital twins of energy infrastructure with integrated geospatial and time-series capabilities.**

.. list-table::
   :widths: auto

   * - License
     - |badge_license|
   * - Documentation
     - |badge_documentation|
   * - Development
     - |badge_issue_open| |badge_issue_closes| |badge_pr_open| |badge_pr_closes|
   * - Community
     - |badge_contributing| |badge_contributors| |badge_repo_counts|

.. contents::
    :depth: 2
    :local:
    :backlinks: top

Purpose
============
**InfDB (Infrastructure Database)** is designed to create comprehensive digital twins of energy infrastructure systems, enabling advanced modeling, analysis, and planning of energy networks. This database system integrates geospatial data with time-series information to provide a complete representation of energy systems.

What is InfDB For?
-----------------
InfDB serves as a foundation for:

- **Energy System Modeling**: Create detailed digital representations of electrical grids, heating networks, and gas infrastructure.
- **Infrastructure Planning**: Support decision-making for future energy infrastructure development and optimization.
- **Scenario Analysis**: Model and compare different energy system configurations and their impacts.
- **Time-Series Integration**: Combine static infrastructure data with dynamic measurements like weather conditions and energy consumption.
- **Geospatial Analysis**: Analyze spatial relationships between energy infrastructure components and their environment.

How It Works
-----------
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

Goal
----
The ultimate goal of InfDB is to provide a robust foundation for energy system digital twins that can:

1. Support complex energy planning scenarios and "what-if" analyses
2. Enable integration of various data sources (weather, market prices, consumption patterns)
3. Facilitate interoperability with simulation and optimization tools
4. Provide insights for more efficient, resilient, and sustainable energy infrastructure

By combining geospatial capabilities with time-series data management, InfDB aims to be a comprehensive solution for researchers, utilities, and planners working on the future of energy systems.


Getting Started
===============
To get started, follow these steps:

Requirements
------------
- Python 3.10 or higher
- Docker and Docker Compose for containerization
- Git for version control (download from https://git-scm.com/)
- PostgreSQL with the following extensions:
  - TimescaleDB for time-series data
  - PostGIS for geospatial data
  - 3DCityDB for urban modeling

Installation for local development
----------------------------------
#. Clone the repository to your local machine:

   .. code-block:: bash

      git clone <repository_url>

#. Set up the virtual environment:

   .. code-block:: bash

      python -m venv venv
      # For Windows
      source venv\Scripts\activate

      # For Linux/MacOS
      source venv/bin/activate


#. Install dependencies:

   .. code-block:: bash

      pip install -r requirements.txt

#. Our application has dependency on 3dCityDB and Timescale; that's why environment should be set first. 
Under `configs` folder we have multiple `config` files that keeps service related inputs.
Information related configuration is explained under `configs/Readme.md`
   
   .. code-block:: bash

    # example for timescaledb
      timescaledb:
        user: timescale_user
        password:
        db: timescaledb_db
        host: 127.0.0.1 
        port: 5432
        status: active

#. To run our databases and feed them with data, we should first run the code below. This will auto generate the `docker-compose.yaml` depending on our needs. 
Information related docker-compose generations is explained under `configs/Readme.md`

   .. code-block:: bash

      # On Linux/macOS
      python3 -m dockers.generate-compose

   .. code-block:: bash

      # On Windows (if python3 doesn't work)
      python -m dockers.generate-compose

#. As a last step we would need to start our services.

   .. code-block:: bash

      docker-compose -f ./dockers/docker-compose.yml up

#. If you had any changes related with loader, you should create the image again if you have an existing image. Then you should do:

   .. code-block:: bash

      docker-compose -f ./dockers/docker-compose.yml up --build

#. Now you can start the application:

   .. code-block:: bash

    fastapi dev src/main.py


Calculating Solar Potantials and Saving Into CityDB v5:
-------------------------------------------------------

#. In the steps above, we went over how to feed InfDB with different data sources which includes LOD2.

#. To run solar potential calculations, we need to first generate and .env file as we have dependencies on dynamic values from dockers/loader.

   .. code-block:: bash

      # On Linux/macOS
      python3 -m  dockers.sunpot.generate-env

   .. code-block:: bash

      # On Windows (if python3 doesn't work)
      python -m  dockers.sunpot.generate-env

#. Assuming CityDB v5 is running on your host machine, now we can start `sunpot` service. It will generate calculations on Citydb v4 and then import those data into CityDB v5. Please run the following command:
   
   .. code-block:: bash

      docker-compose -f ./dockers/sunpot/docker-compose.yml up

#. If you had any changes in the codes under `src/services/sunpot/`, please build the image again and run the compose project.

   .. code-block:: bash

      docker-compose -f ./dockers/sunpot/docker-compose.yml up --build

#. Services should be running sequentially once CityDB v4 is ready.

Repository Structure
====================

- **src/**: Main application package
  - **api/**: API endpoints (cityRouter.py, weatherRouter.py)
  - **core/**: Core application code (dbConfig.py, etc.)
  - **db/**: Database models and repositories
    - **models/**: SQLModel classes for database entities
    - **repositories/**: Data access layer for database operations
  - **exceptions/**: Custom exception classes
  - **externals/**: External API integrations (e.g., weather API)
  - **schemas/**: Data schemas and validation
  - **services/**: Business logic services
  - **main.py**: Application entry point
- **docs/**: Documentation
  - **architecture/**: System architecture documentation
  - **contributing/**: Contribution guidelines and code of conduct
  - **development/**: Developer guides and workflows
  - **guidelines/**: Project guidelines and standards
  - **operations/**: Operational guides and CI/CD documentation
  - **source/**: Source files for documentation
  - **img/**: Images used in documentation
- **dockers/**: Docker configuration files
- **tests/**: Test suite
  - **unit/**: Unit tests for individual components
  - **integration/**: Tests for component interactions
  - **e2e/**: End-to-end tests for the application
  - **conftest.py**: Pytest configuration and fixtures


Usage Guidelines
================

Basic API Usage
--------------

InfDB provides a RESTful API for interacting with energy infrastructure data:

#. **City Data API**: Access 3D city model data and raster information

   .. code-block:: bash

      # Generate rasters at a specific resolution
      curl -X POST "http://localhost:8000/city/rasters?resolution=100"

      # Get all raster centers at a specific resolution
      curl -X GET "http://localhost:8000/city/rasters?resolution=100"

      # Get the raster center for a specific building
      curl -X GET "http://localhost:8000/city/rasters/building/123?resolution=100"

#. **Weather Data API**: Access time-series weather data linked to spatial regions

   .. code-block:: bash

      # Insert historical weather data
      curl -X POST "http://localhost:8000/weather/weather-data/100" \
         -H "Content-Type: application/json" \
         -d '{"dateRange": {"startDate": "2023-01-01", "endDate": "2023-01-31"}, "sensorNames": ["temperature", "humidity"]}'

      # Get weather data for a specific building and time range
      curl -X GET "http://localhost:8000/weather/weather-data/100?buildingId=123&startTime=2023-01-01T00:00:00&endTime=2023-01-31T23:59:59"

Development Workflow
-------------------
#. **Set up the environment** following the installation instructions.
#. **Open an issue** to discuss new features, bugs, or changes.
#. **Create a new branch** for each feature or bug fix based on an issue.
#. **Implement the changes** following the coding guidelines.
#. **Write tests** for new functionality or bug fixes.
#. **Run tests** to ensure the code works as expected.
#. **Create a merge request** to integrate your changes.
#. **Address review comments** and update your code as needed.
#. **Merge the changes** after approval.

API Documentation
===============
FastAPI provides built-in OpenAPI documentation for exploring and testing the API:

- **Swagger UI**: Access interactive API documentation at http://127.0.0.1:8000/docs
- **ReDoc**: View alternative API documentation at http://127.0.0.1:8000/redoc

The documentation includes:

- Detailed endpoint descriptions
- Request and response schemas
- Authentication requirements
- Example requests
- Try-it-out functionality for testing endpoints directly

You can also download the OpenAPI specification in JSON format at http://127.0.0.1:8000/openapi.json


CI/CD Workflow
==============

The CI/CD workflow is set up using GitLab CI/CD.
The workflow runs tests, checks code style, and builds the documentation on every push to the repository.
You can view workflow results directly in the repository's CI/CD section.
For detailed information about the CI/CD workflow, see the `CI/CD Guide <docs/operations/CI_CD_Guide.md>`_.

Development Resources
=====================
The following resources are available to help developers understand and contribute to the project:

Coding Guidelines
-----------------
The `Coding Guidelines <docs/guidelines/coding_guidelines.md>`_ document outlines the coding standards and best practices for the project.
Start here when trying to understand the project as a developer.

Architecture Documentation
--------------------------
The `Architecture Documentation <docs/architecture/index.rst>`_ provides an overview of the system architecture, including the database schema, components, and integration points.

Developer Guides
----------------
- `Development Setup Guide <docs/development/setup.md>`_: Comprehensive instructions for setting up a development environment
- `Contribution Workflow <docs/development/workflow.md>`_: Step-by-step process for contributing to the project
- `API Development Guide <docs/development/api_guide.md>`_: Information for developers who want to use or extend the API
- `Database Schema Documentation <docs/development/database_schema.md>`_: Detailed information about the database schema

Contribution Guidelines
-----------------------
- `Contributing Guide <docs/contributing/CONTRIBUTING.md>`_: Guidelines for contributing to the project
- `Code of Conduct <docs/contributing/CODE_OF_CONDUCT.md>`_: Community standards and expectations
- `Release Procedure <docs/contributing/RELEASE_PROCEDURE.md>`_: Process for creating new releases

Operations Documentation
------------------------
- `CI/CD Guide <docs/operations/CI_CD_Guide.md>`_: Detailed information about the CI/CD workflow

Contribution and Code Quality
=============================
Everyone is invited to develop this repository with good intentions.
Please follow the workflow described in the `CONTRIBUTING.md <docs/contributing/CONTRIBUTING.md>`_.

Coding Standards
----------------
This repository follows consistent coding styles. Refer to `CONTRIBUTING.md <docs/contributing/CONTRIBUTING.md>`_ and the `Coding Guidelines <docs/guidelines/coding_guidelines.md>`_ for detailed standards.

Pre-commit Hooks
----------------
Pre-commit hooks are configured to check code quality before commits, helping enforce standards.

Changelog
---------
The changelog is maintained in the `CHANGELOG.md <CHANGELOG.md>`_ file.
It lists all changes made to the repository.
Follow instructions there to document any updates.

License and Citation
====================
| The code of this repository is licensed under the **MIT License** (MIT).
| See `LICENSE <LICENSE>`_ for rights and obligations.
| See the *Cite this repository* function or `CITATION.cff <CITATION.cff>`_ for citation of this repository.
| Copyright: `TU Munich - ENS <https://www.epe.ed.tum.de/en/ens/homepage/>`_ | `MIT <LICENSE>`_


.. |badge_license| image:: https://img.shields.io/badge/license-MIT-blue
    :target: LICENSE
    :alt: License

.. |badge_documentation| image:: https://img.shields.io/badge/docs-available-brightgreen
    :target: https://gitlab.lrz.de/tum-ens/need/database
    :alt: Documentation

.. |badge_contributing| image:: https://img.shields.io/badge/contributions-welcome-brightgreen
    :target: docs/contributing/CONTRIBUTING.md
    :alt: contributions

.. |badge_contributors| image:: https://img.shields.io/badge/contributors-0-orange
    :alt: contributors

.. |badge_repo_counts| image:: https://img.shields.io/badge/repo-count-brightgreen
    :alt: repository counter

.. |badge_issue_open| image:: https://img.shields.io/badge/issues-open-blue
    :target: https://gitlab.lrz.de/tum-ens/need/database/-/issues
    :alt: open issues

.. |badge_issue_closes| image:: https://img.shields.io/badge/issues-closed-green
    :target: https://gitlab.lrz.de/tum-ens/need/database/-/issues
    :alt: closed issues

.. |badge_pr_open| image:: https://img.shields.io/badge/merge_requests-open-blue
    :target: https://gitlab.lrz.de/tum-ens/need/database/-/merge_requests
    :alt: open merge requests

.. |badge_pr_closes| image:: https://img.shields.io/badge/merge_requests-closed-green
    :target: https://gitlab.lrz.de/tum-ens/need/database/-/merge_requests
    :alt: closed merge requests
