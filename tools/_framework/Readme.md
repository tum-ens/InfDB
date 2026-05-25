# InfDB Dev Container Template

A reusable template for creating Docker-based development containers that interact with the InfDB infrastructure. This template provides a standardized structure for importing (eg. infdb-laoder) data,  processing tools (eg infdb-basedata), and analysis scripts (kwp) that work with the InfDB PostgreSQL/PostGIS database.

## Overview

This template enables you to:
- Quickly scaffold new InfDB tools with consistent structure
- Access InfDB database connections with pre-configured clients
- Run Python scripts with geospatial capabilities (GeoPandas, SQLAlchemy)
- Execute SQL scripts for database operations
- Develop with VS Code dev containers for debugging

## Workflow
Each tool in the InfDB infrastructure operates in its own isolated database schema, named after the tool itself. This schema isolation ensures that multiple developers can work independently without interfering with each other's data or processes.

### Schema Isolation

```
PostgreSQL Database (infdb)
│
├── Schema: infdb-import          # Data import tool
│   ├── Tables
│   ├── Views
│   └── Functions
│
├── Schema: infdb-basedata        # Base data processing
│   ├── Tables
│   ├── Views
│   └── Functions
│
├── Schema: kwp                   # Analysis scripts
│   ├── Tables
│   ├── Views
│   └── Functions
│
└── Schema: choose-a-name         # Your new tool
   ├── Tables
   ├── Views
   └── Functions
```

The schema name is automatically configured from your tool name and available in SQL scripts via the `{output_schema}` template variable.

## Getting Started
### Run your tool

Prerequisites:
- [Docker Desktop](https://docs.docker.com/get-started/get-docker/) (or Docker Engine) installed
- Follow [development workflow instructions](#development-workflow) below
- Run commands from the repository root

**Option A — Docker Compose:**
Start tool
```bash
docker compose -f tools/choose-a-name/compose.yml up
```

**Option B — VS Code Dev Containers:**
1. Open created tool folder in [*Visual Studio Code*](https://code.visualstudio.com/download): File → → Open Folder... → `tools/choose-a-name`
2. Install the “Dev Containers” extension
3. Press F1 → “Dev Containers: Reopen in Container”
4. Run and debug (F5) with breakpoints in Python

**Hint**: If there is an error on startup while building since dev container already exists by using **Option A**, then delete it before manually:
```bash
# Remove docker
docker compose -f tools/choose-a-name/compose.yml down
```

## Project Structure

```
choose-a-name/
├── src/                                    # Python source modules
│   └── demo.py                             # Example database operations
│   └── template.py                         # Template python file for your own code
├── sql/                                    # SQL scripts (alphabetical order)
│   └── 00_cleanup.sql                      # Schema initialization
│   └── 01_template.sql                     # Template sql file for your own code
├── configs/                                # Configuration files
│   └── config-choose-a-name.yml            # Tool-specific config
├── main.py                                 # Entry point - starts here
├── pyproject.toml                          # Python dependencies
├── compose.yml                             # Docker Compose definition
├── create_new_tool.yml                     # Creates new tool based on infdb-template
├── Dockerfile                              # Docker image build
├── .env                                    # Environment variables
├── Readme_template.md                      # Readme for tool users
└── Readme.md                               # Readme for tool developers
```

### Key Files

#### `main.py`
Entry point that:
- Initializes InfDB client (Sets up logging, database connections, etc.)
- Executes your business logic

#### `src/demo.py`
Example functions showing:
- SQL script execution with InfDB
- Database queries with InfDB client
- Direct SQLAlchemy connections
- GeoPandas spatial data integration

#### `sql/*.sql`
SQL scripts for database operations:
- Execute in alphabetical order (use prefixes: `01_`, `02_`)
- Support template variables like `{output_schema}`, `{input_schema}`
- Useful for schema setup, transformations, indexes

#### `pyproject.toml`
Python project configuration:
- Package dependencies
- Python version requirements
- Build system configuration

#### `compose.yml`
Docker Compose service definition:
- Container configuration
- Volume mounts
- Network settings
- Environment variables

### Development Workflow

1. **Define tool name:**
   - Think of a tool name
   - Use kebab-case naming convention as for example "choose-a-name" 

2. **Create Dev Container:**
   ```bash
   # Replace choose-a-name
   bash tools/_infdb-template/create_new_tool.sh choose-a-name
   ```

5. **Add dependencies:**
   - Add needed package into **dependencies** in `tools/choose-a-name/pyproject.toml`.
   - Run `uv sync` in order to update virtual environment with new packages or (re-start) docker via `docker compose -f tools/choose-a-name/compose.yml up`

6. **Implement your code:**
   - **Python:** Add your code to `src/`
   - **SQL:** Add your scripts to `sql/` - We recommend adding numbers according to the execution order (executed in alphabetical order)
   - **Execution:** Start your added python code btw. sql scripts in `main.py`. The sql files can be easily executed as shown in `src/demo.py`. This spllting ensures clarity and easy overview what is executed.

7. **Document your code:**
   - Add docstrings and comments to your code
   - Update Readme_template.md for user of your tool

## Known issues

- **Devcontainer Python interpreter not used:** If the venv from `.devcontainer/devcontainer.json` (`python defaultInterpreterPath`) isn’t active, check VS Code **User/Remote** settings for `python.defaultInterpreterPath` (may override). Reopen the devcontainer and run **Python: Select Interpreter**.

