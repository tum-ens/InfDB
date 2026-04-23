# Infdb

## `InfDB`

Facade for configuration, logging, and DB connections for InfDB.

Other repos (e.g., `infdb-import`, `infdb-basedata`) should import and use this
class as the single entry point.

### `__init__(tool_name: str, config_path: str = DEFAULT_CONFIG_DIR) -> None`

Initialize the facade with configuration and logging.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `tool_name` | `str` | Identifier used to pick the tool section in the config. | *required* |
| `config_path` | `str` | Base directory containing YAML configuration files. | `DEFAULT_CONFIG_DIR` |

### `get_logger() -> logging.Logger`

Return the root logger used by this instance.

### `get_worker_logger() -> logging.Logger`

Create and return a worker logger from the InfdbLogger helper.

### `stop_logger() -> None`

Stop the InfdbLogger's QueueListener.

### `connect() -> InfdbClient`

Create a new database client.

Prefer: `with inf.connect(...) as client: ...`.

Args: None

Returns:

| Type | Description |
| --- | --- |
| `InfdbClient` | An InfdbClient connected to the requested database. |

### `get_db_engine()`

Return a SQLAlchemy engine for the specified database.

Args: None

Returns:

| Type | Description |
| --- | --- |
|  | A SQLAlchemy Engine instance connected to the same target DB. |

### `get_toolname() -> str`

Return the tool name configured for this instance.

### `get_config_dict() -> Dict[str, Any]`

Return the merged configuration dictionary.

### `get_db_parameters_dict() -> Dict[str, Any]`

Return final parameters dictionary for the postgres service.

### `get_config_value(keys: List[str], insert_toolname: bool = False)`

Return a value from the configuration by traversing a key path.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `keys` | `List[str]` | Ordered key path within the configuration. | *required* |
| `insert_toolname` | `bool` | If True, prepend the tool name to the key path. | `False` |

Returns:

| Type | Description |
| --- | --- |
|  | The value at the specified path, or None if missing. |

### `get_config_path(keys: List[str], type: str = 'config', insert_toolname: bool = False) -> str`

Resolve a filesystem path from config.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `keys` | `List[str]` | Ordered key path within the configuration. | *required* |
| `insert_toolname` | `bool` | If True, prepend the tool name to the key path. | `False` |

Returns:

| Type | Description |
| --- | --- |
| `str` | An absolute filesystem path. |

### `get_env_variable(key) -> Optional[str]`

Return a dictionary of environment variables for this tool.

Returns:

| Type | Description |
| --- | --- |
| `Optional[str]` | A dictionary of environment variables. |
