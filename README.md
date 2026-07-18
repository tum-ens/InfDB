<p align="center">
   <img src="docs/mkdocs/docs/assets/img/logo_infdb.png" alt="Repo logo" width="100"/>
</p>

# InfDB - Energy and Infrastructure Database Ecosystem
**InfDB - Energy and Infrastructure Database Ecosystem** provides a modular and easy-to-configure open-source data and tool infrastructure. It is equipped with essential services, designed to minimize the effort required for data management. We follow a platform-independent containerized approach that streamlines collaboration in energy modeling and analysis, empowering the growth of an ecosystem by offering standardized interfaces and APIs, and by allowing users to dedicate their focus to generating insights rather than handling data logistics.

| Category | Badges |
|----------|--------|
| License | [![License](https://img.shields.io/badge/license-Apache%202-blue)](LICENSE) |
| Publication | [![JOSS](https://joss.theoj.org/papers/10.21105/joss.10458/status.svg)](https://doi.org/10.21105/joss.10458) |
| Documentation | [![Documentation](https://img.shields.io/badge/docs-available-brightgreen)](https://tum-ens.github.io/InfDB) |
| Community | [![Contributing](https://img.shields.io/badge/contributions-welcome-brightgreen)](https://tum-ens.github.io/InfDB/development) [![Contributors](https://img.shields.io/github/contributors/tum-ens/InfDB)](https://github.com/tum-ens/InfDB/graphs/contributors) [![Last Commit](https://img.shields.io/github/last-commit/tum-ens/InfDB)](https://github.com/tum-ens/InfDB/commits/) |

## Table of Contents

- [Why use it?](#why-use-it)
- [How it works?](#how-it-works)
- [Getting Started](#getting-started)
- [License and Citation](#license-and-citation)

## Why use it?
InfDB addresses common challenges in energy system modeling and analysis, particularly those related to data management. By providing a standardized and modular infrastructure, InfDB reduces the time and effort required to set up and maintain data systems. This allows researchers, analysts, and planners to focus on their core tasks of modeling and analysis, rather than being bogged down by data logistics.

InfDB can be used effectively wherever geospatial and time series information is required. Possible applications include:

-   Energy System Modeling
-   Municipal Heat Planning and Infrastructure Planning
-   Scenario and Geospatial Analysis

## How it works?
InfDB consists of the following layers:

- **Services** – Dockerized open-source software providing base functionality.
- **Tools** –  Software interacting with InfDB.
- **Python API** –  Python package pyinfdb for interacting with InfDB.

![InfDB overview](docs/mkdocs/docs/assets/img/infdb-overview.png)

### Services
The InfDB platform provides a suite of essential services designed to facilitate database operation and administration, data handling and visualization, and connectivity. Each preconfigured service can be activated individually to tailor the environment to your specific requirements.

More information, a list of available services see [Services](https://tum-ens.github.io/InfDB/infdb/#services).

### Tools
Tools are software that interact with InfDB and process data through standardized, open interfaces. This modular approach allows you to tackle problems of any complexity by combining different tools into custom toolchains.

More information, a list of integrated tools and additional information, see [Tools](https://tum-ens.github.io/InfDB/tools/).

## Getting Started
If you want to use the InfDB with the default settings just use the [Quick Start](#quick-start) below. For more information in detail read the [Usage Guide](https://tum-ens.github.io/InfDB/usage/) of the official documentation.

### Prerequisites
 - Docker Engine: https://docs.docker.com/engine/install/
 - Docker Desktop: https://docs.docker.com/desktop/

#### Local Folder Structure
The InfDB allows a modular folder structure to manage multiple database instances independently. Each instance represents a separate deployment with its own data, configuration, and services—ideal for handling different regions, projects, or environments.
```
infdb/
├── infdb-demo/
├── muenchen/
├── bavaria/
├── grid-planning/
└── ...
```
The recommended structure places all instance data in docker managed volumes while keeping each instance's configuration and tools in separate directories (e.g. by region `muenchen/`, `bavaria/`). This approach simplifies backups, migrations, and multi-instance management.

#### Configuration
The configuration of services is managed through environment variables set in the environment file `.env` and for data import in the YAML file `configs/config-infdb-import.yml`. The environment file controls which services are activated and their settings, while the YAML file specifies which datasets are imported and how they are processed. If no configuration is provided, the InfDB will create an environment file as well as a YAML file with default settings. More details can be found in section [Setup](https://tum-ens.github.io/InfDB/usage/setup/) of the documentation.

Default configuration settings and the database service activated:
```bash title=".env"
# ==============================================================================
# SERVICE ACTIVATION
# ==============================================================================
# Select profiles to activate
COMPOSE_PROFILES=db  # db,admin,notebook,qwc,api

# ==============================================================================
# POSTGRESQL DATABASE (Db Service)
# ==============================================================================
# Profile: db

# Database name
SERVICES_POSTGRES_DB=infdb

# Database credentials
SERVICES_POSTGRES_USER=infdb_user
SERVICES_POSTGRES_PASSWORD=infdb

# Host:Port address from which a container is able to reach the Postgres database
SERVICES_POSTGRES_HOST=host.docker.internal
SERVICES_POSTGRES_EXPOSED_PORT=54328

# EPSG code for spatial reference system (25832 = ETRS89 / UTM zone 32N)
SERVICES_POSTGRES_EPSG=25832
```

### Quick Start
You can quickly start InfDB with default configuration and credentials as mentioned above by following these steps:

First of all, create the main `infdb` directory and navigate into it:
```bash
mkdir infdb
cd infdb
```

#### Clone InfDB
``` bash
# Replace "infdb-demo" by name of instance 
git clone --recurse-submodules https://github.com/tum-ens/InfDB.git infdb-demo
cd infdb-demo
```

#### Start InfDB
```bash
bash infdb.sh start
```

#### Import Opendata
```bash
bash infdb.sh import
```

#### Stop InfDB
```bash
bash infdb.sh stop
```

#### Run Tools
Once InfDB has been successfully started and data has been imported, you can use the integrated tools or develop your own using the provided tool framework to interact with InfDB data. Detailed information on available tools and their usage is provided in the [Tools](https://tum-ens.github.io/InfDB/tools/) section of the documentation.

To run the Linear Heat Density demo, execute:
```bash
uv run python3 tools/tools.py -p linear
```
Additional information is available in the [Linear Heat Density](https://tum-ens.github.io/InfDB/linear-heat-density/) section of the documentation.

To see the outputs of executing the tool you may, for example, review the Postgres database. If you have default configuration, you can run the following:
```bash
$ docker ps  # To get the ID of the container
$ docker exec -it <container ID> bash  # Start a new shell session in the container
$ psql --username=infdb_user -W --dbname=infdb  # Executed inside the container where password is found in config
```
Once inside the Postgres database within the Docker container:
```sql
SELECT * FROM linear_heat_density.linear_heat_density LIMIT 10;
```

You can also use pgAdmin or any other database client to connect to the database using the credentials and port specified in the configuration.

# Changelog

The changelog is maintained in the [CHANGELOG.md](CHANGELOG.md) file. It lists all changes made to the repository. Follow instructions there to document any updates.

# License and Citation

The code of this repository is licensed under the **Apache 2.0 License**.  
See [LICENSE](LICENSE) for rights and obligations.  
Copyright: [TU Munich - ENS](https://www.epe.ed.tum.de/en/ens/homepage/) | [Apache 2.0 License](LICENSE)

If you use InfDB in your work, please cite the paper published in the *Journal of Open Source Software*:

> Buchenberg et al., (2026). InfDB: An Open Source Energy and Infrastructure Data Ecosystem for Modeling and Planning. *Journal of Open Source Software*, 11(122), 10458, https://doi.org/10.21105/joss.10458

See [Citation](docs/mkdocs/docs/welcome/citation.md) for the BibTeX entry and for citing a specific software version.

# Contact
Patrick Buchenberg

Chair of Renewable and Sustainable Energy System
Technical University of Munich (TUM) 
Email: patrick.buchenberg@tum.de
[https://www.epe.ed.tum.de/ens/staff/ensteam/patrick-buchenberg/](https://www.epe.ed.tum.de/ens/staff/ensteam/patrick-buchenberg/)