# Repository Strucuture

![Repository Structure](repository-structure.png)

<!-- ### Root Directory
- **Configuration Files**: `.env`, `.env.template`, `pyproject.toml`, `pytest.ini`, `uv.lock`
- **Docker Files**: `compose.yml`, `.dockerignore`
- **Version Control**: `.git/`, `.github/`, `.gitlab/`, `.gitignore`, `.gitmodules`
- **CI/CD**: `.gitlab-ci.yml`, `.pre-commit-config.yaml`, `.readthedocs.yml`
- **Shell Scripts**: `infdb-import.sh`, `infdb-remove.sh`, `infdb-start.sh`, `infdb-stop.sh`
- **Documentation**: `CHANGELOG.md`, `CITATION.cff`, `GEMINI.md`, `LICENSE`, `Readme.md`, `VERSION` -->

### Main Directories

#### `.github/`
GitHub-specific configurations including issue templates, pull request templates, and CI workflows.

#### `.gitlab/`
GitLab-specific configurations including issue templates, merge request templates, and CI workflows.

#### `configs/`
Configuration files for InfDB initialization:

- `config-infdb-import.yml`: Configuration for infdb-import to import opendata sources

#### `docs/`

- **mkdocs/**: MkDocs-based documentation with comprehensive guides on API, development, InfDB architecture, tools, usage, and welcome information
- **data-bugs.md**: Collection of known data issues and bugs

#### `services/`
InfDB services, each with Docker configurations:

- **infdb-api/**: API services (FastAPI, PostgREST, pygeoapi)
- **infdb-db/**: PostgreSQL database with 3DCityDB extension
- **infdb-http/**: HTTP server with nginx
- **infdb-import/**: Data import service with various data source importers
- **jupyter/**: Jupyter notebook service for analysis
- **opencloud/**: Nextcloud integration
- **pgadmin/**: PostgreSQL administration interface
- **qgis_webclient/**: QGIS web client for GIS visualization

#### `src/`
Main application package:

- **infdb_package/**: Python package with core InfDB functionality
    - **infdb/**: Core modules (client, config, logger, utils)
    - **scripts/**: Utility scripts for documentation and API generation
    - **docs/** & **documentation/**: Package-specific documentation

#### `tests/`
Test suite organized by type:

- **ci/**: Continuous integration tests
- **e2e/**: End-to-end tests
- **integration/**: Integration tests
- **unit/**: Unit tests

#### `tools/`
External analysis and processing tools:

- **_infdb-template/**: Template for creating new tools
- **buildings-to-street/**: Building to street mapping
- **infdb-basedata/**: Base data management with Liquibase
- **infdb-metadata/**: Metadata management
- **kwp/**: Heat capacity calculations
- **linear-heat-density/**: Linear heat density calculations
- **process-streets/**: Street network processing
- **ro-heat/**: Building thermal resistance calculations
- **sunpot/**: Solar potential analysis

Each tool typically contains:

- Docker configuration (`Dockerfile`, `compose.yml`)
- Python entry point (`main.py`)
- Configuration files in `configs/`
- SQL scripts in `sql/`
- Source code in `src/`
- Development environment configurations (`.devcontainer/`, `.vscode/`)