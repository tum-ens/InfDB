# Python Package pyinfdb
This guide explains how to use the `pyinfdb` python package to interact with your InfDB instance.

## Structure
The `pyinfdb` package consists of a superior class InfDB based on the internal classes InDBConfig, InfDBClient, InfDBLogger and InfDBIO as shown in the following figure:
![alt text](pyinfdb.png)
The user only interacts with the superior InfDB class, the internal classes are not directly accessible. This abstraction ensures the python interface is consistent despite changes in the internal structure of the package.
It provides functions for database access, configuration management, logging and data handling. The central idea is to provide standard methods to interact with InfDB in order to simplify the interaction with InfDB.

## Installation
pyinfdb is available on [PyPI](https://pypi.org/project/infdb/) and can be installed via pip:
```bash
uv pip install pyinfdb
```

## Quick Start
The typical workflow involves three steps:

1.  **Configuration**: Define via YAML or environment file.
2.  **Initialize InfDB**: Create an instance of the `InfDB` class.
3.  **Usage**: Use the instance to get a database connection and log messages.

### 1. Configuration
The InfDB class uses system environment variables and YAML configuration files to load the database credentials, settings and parameters. If no path is given, no configuration will be loaded and the configuration will rely solely on environment variables. Otherwise, the configuration file path needs to be given as the argument `config_path` while initializing the InfDB class. A typical config file (e.g., `configs/config-my-tool.yml`) looks like this:
```yaml title="config-my-tool.yml"
db:
  host: None        #(1)
  port: None        #(1)
  user: None        #(1)
  password: None    #(1)
  dbname: None      #(1)

logging:
  level: INFO       #(2)
  path: logs/my_tool.log
```

1. Replace with your database port or set to None to rely on environment variables
2. Set logging level: `ERROR`, `WARNING`, `INFO`, `DEBUG`

Configuration paramters that should be not overridden can be set to "None" in the config file. This ensures that these parameters are not accidentally changed and that the system environment variables are used instead. This is especially useful for sensitive information such as database credentials.

Environment variables can be set in a `.env` file or directly in the system environment. The excerpt below shows the central .env file for InfDB, which contains the database credentials and connection parameters.
```bash title=".env"
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

### 2. Initialization
Import `pyinfdb` and initialize the `InfDB` class. You must provide a `tool_name`. If no tool name is provided, the InfDB instance will rely solely on environment variables for configuration.

```python
from pyinfdb import InfDB

infdb = InfDB(tool_name="choose-a-name") #(1)
log = infdb.get_logger()
```

1. Optional: Provide a tool name to load specific configuration `config_path="config-choose-a-name.yml"`.

### 3. Usage
Here are some examples of how to use the `InfDB` instance to get a database connection and log messages.

```python
log.info("Starting processing...")
try:
    with infdb.connect() as client: #(1)
        
        rows = client.execute_query("SELECT * FROM my_table LIMIT 5") #(2)
        for row in rows:
            log.debug(row)
            
        client.execute_file("scripts/setup_schema.sql") # (3)
except Exception as e:
    log.error(f"An error occurred: {e}")
```

1. Uses the credentials and connection parameters from the YMAL configuration file or system environment variables to establish a connection to the database.
2. Execute a SQL query and log the results.
3. Execute a SQL script from a file.