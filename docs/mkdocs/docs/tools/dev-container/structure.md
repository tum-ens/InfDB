# Project Structure

```
tools/
└── choose-a-name/
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

## Key Files

### `main.py`
Entry point that:
- Initializes InfDB client (Sets up logging, database connections, etc.)
- Executes your business logic

### `src/demo.py`
Example functions showing:

- SQL script execution with InfDB
- Database queries with InfDB client
- Direct SQLAlchemy connections
- GeoPandas spatial data integration

### `sql/*.sql`
SQL scripts for database operations:

- Execute in alphabetical order (use prefixes: `01_`, `02_`)
- Support template variables like `{output_schema}`, `{input_schema}`
- Useful for schema setup, transformations, indexes

### `pyproject.toml`
Python project configuration:

- Package dependencies
- Python version requirements
- Build system configuration

### `compose.yml`
Docker Compose service definition:

- Container configuration
- Volume mounts
- Network settings
- Environment variables