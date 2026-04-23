# Config

## `InfdbConfig`

Read and resolve tool-specific YAML config with optional InfDB base merge.

### `__init__(tool_name: str, config_basedir: Optional[str] = DEFAULT_CONFIG_DIR) -> None`

Initialize configuration for a tool.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `tool_name` | `str` | The tool identifier (used to select the YAML file and section). | *required* |
| `config_basedir` | `Optional[str]` | Base directory containing config files (defaults to 'configs'). | `DEFAULT_CONFIG_DIR` |

### `get_config() -> Dict[str, Any]`

Return the fully merged and resolved configuration dictionary.

### `get_value(keys: List[str]) -> Any`

Safely traverse nested keys; returns None if the path is missing.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `keys` | `List[str]` | Ordered key path within the configuration. | *required* |

Returns:

| Type | Description |
| --- | --- |
| `Any` | The value at the specified path, or None if any segment is missing. |

Raises:

| Type | Description |
| --- | --- |
| `ValueError` | If keys is empty. |

### `get_path(keys: List[str], type: str) -> str`

Resolve a path from config and map it to a filesystem location.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `keys` | `List[str]` | Ordered key path within the configuration. | *required* |
| `type` | `str` | One of {'loader', 'heat', 'package', 'setup'} controlling base dir. | *required* |

Returns:

| Type | Description |
| --- | --- |
| `str` | Absolute filesystem path derived from the config value. |

### `get_root_path() -> str` `staticmethod`

Return the project root path (two levels up from this file).

### `get_db_parameters(db_name: str = 'postgres') -> Dict[str, str]`

Return database connection parameters for a given service from config-toolname.yml.
Adopt it from environment variables if set to "None".
Host is set to "host.docker.internal" if "None".

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `db_name` | `str` | Name of the DB service section to read. | `'postgres'` |

Returns:

| Type | Description |
| --- | --- |
| `Dict[str, str]` | Final parameters dictionary for the requested service. |

### `get_env_parameters(key, infdb) -> Optional[str]`

Return a dictionary of environment variables for this tool.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `key` |  | Environment variable name (case-insensitive). | *required* |
| `infdb` |  | An InfDB object used for logging. | *required* |

Returns:

| Type | Description |
| --- | --- |
| `Optional[str]` | A dictionary of environment variables. |

Raises:

| Type | Description |
| --- | --- |
| `ValueError` | If the environment variable `key.upper()` is not set. |
