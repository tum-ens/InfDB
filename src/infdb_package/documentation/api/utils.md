# Utils

## `read_env(var_name: str, default: Optional[str] = None, required: bool = False) -> str`

Read an environment variable with optional default and required check.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `var_name` | `str` | Name of the environment variable to read. | *required* |
| `default` | `Optional[str]` | Value to return if the environment variable is not set. | `None` |
| `required` | `bool` | If True, treat a missing or empty value as an error and exit. | `False` |

Returns:

| Type | Description |
| --- | --- |
| `str` | The environment variable value, or `default` if it is not set. If `required` is True and the value is missing/empty, the function does not return. |

Raises:

| Type | Description |
| --- | --- |
| `SystemExit` | Exits with status code 2 if `required` is True and the variable is missing or empty. |

## `build_dsn_from_env(user_var: str, pwd_var: str, db_var: str, host_var: str, port_var: int) -> str`

Build a PostgreSQL DSN string from common environment variables.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `user_var` | `str` | Database username. | *required* |
| `pwd_var` | `str` | Database password. | *required* |
| `db_var` | `str` | Database name. | *required* |
| `host_var` | `str` | Database host. | *required* |
| `port_var` | `int` | Database port. | *required* |

Returns:

| Type | Description |
| --- | --- |
| `str` | A PostgreSQL connection URL (DSN) in the form: `postgresql://<user>:<password>@<host>:<port>/<db>`. |

## `ensure_dir_exists(path: str) -> str`

Ensure a directory (or a file's parent directory) exists; return absolute path.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `path` | `str` | A directory path or a file path. | *required* |

Returns:

| Type | Description |
| --- | --- |
| `str` | The absolute version of `path`. |

Raises:

| Type | Description |
| --- | --- |
| `ValueError` | If `path` is an empty string. |

## `atomic_write_text(text: str, output_path: str, file_mode: str | None = None, dir_mode: str | None = None) -> str`

Atomically write text to a file. Optionally apply chmod to file/dir.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `text` | `str` | Text content to write. | *required* |
| `output_path` | `str` | Destination file path (absolute or relative). Parent directories will be created if needed. | *required* |
| `file_mode` | `str | None` | Optional file permission mode (octal string, e.g. `"644"` or `"600"`). | `None` |
| `dir_mode` | `str | None` | Optional directory permission mode (octal string) to apply to the destination directory. | `None` |

Returns:

| Type | Description |
| --- | --- |
| `str` | The absolute path of the written file. |

Raises:

| Type | Description |
| --- | --- |
| `ValueError` | If `output_path` is empty. |
| `OSError` | If writing, syncing, or replacing the file fails (and potentially if applying `file_mode` fails). |

## `atomic_write_yaml(data: Any, output_path: str, file_mode: str | None = None, dir_mode: str | None = None) -> str`

Atomically serialize a Python object to YAML and write to a file.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `data` | `Any` | Python object to serialize to YAML (e.g., dict, list). | *required* |
| `output_path` | `str` | Destination file path (absolute or relative). Parent directories will be created if needed. | *required* |
| `file_mode` | `str | None` | Optional file permission mode (octal string, e.g. `"644"` or `"600"`). | `None` |
| `dir_mode` | `str | None` | Optional directory permission mode (octal string) to apply to the destination directory. | `None` |

Returns:

| Type | Description |
| --- | --- |
| `str` | The absolute path of the written YAML file. |

Raises:

| Type | Description |
| --- | --- |
| `ValueError` | If `output_path` is empty. |
| `YAMLError` | If the object cannot be serialized to YAML. |
| `OSError` | If writing, syncing, or replacing the file fails (and potentially if applying `file_mode` fails). |

## `read_text(input_path: str) -> str`

Read a text file; return empty string if it does not exist.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `input_path` | `str` | Path to the file to read. | *required* |

Returns:

| Type | Description |
| --- | --- |
| `str` | The file contents as a string. If the file does not exist, returns an empty string. |

Raises:

| Type | Description |
| --- | --- |
| `OSError` | For IO errors other than `FileNotFoundError` (e.g., permission denied). |

## `write_yaml(data: Any, output_path: str) -> None`

Backward-compatible non-atomic YAML writer.
Prefer `atomic_write_yaml` for config files.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `data` | `Any` | Python object to serialize to YAML (e.g., dict, list). | *required* |
| `output_path` | `str` | Destination file path (absolute or relative). Parent directories will be created if needed. | *required* |

Returns:

| Type | Description |
| --- | --- |
| `None` | None. |

Raises:

| Type | Description |
| --- | --- |
| `ValueError` | If `output_path` is invalid (propagated from `ensure_dir_exists`). |
| `YAMLError` | If the object cannot be serialized to YAML. |
| `OSError` | If the file cannot be opened or written (e.g., permission denied). |

## `do_cmd(cmd: str | List[str], is_shell_interpreted: bool = False) -> int`

Execute a shell command, streaming output to the logger.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `cmd` | `str | List[str]` | Command to run. Can be a string or a list of strings. | *required* |
| `is_shell_interpreted` | `bool` | If True, run command through the shell. Default is False for security. **Warning:** Setting is\_shell\_interpreted=True is considered unsafe in general and should be used with caution! | `False` |

Returns:

| Type | Description |
| --- | --- |
| `int` | The process exit code (0 indicates success; non-zero indicates failure). |

Raises:

| Type | Description |
| --- | --- |
| `ValueError` | If `cmd` is empty. |
| `OSError` | If the process cannot be started (e.g., command not found). |

## `do_sql_query(query: str, cfg: InfdbConfig, db_name: str = DEFAULT_DB_NAME, logger: Optional[logging.Logger] = None) -> None`

Run a single SQL statement using InfdbClient, then close the connection.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `query` | `str` | SQL statement to execute. | *required* |
| `cfg` | `InfdbConfig` | `InfdbConfig` instance used to resolve database connection parameters. | *required* |
| `db_name` | `str` | Name of the database to connect to. Defaults to `DEFAULT_DB_NAME`. | `DEFAULT_DB_NAME` |
| `logger` | `Optional[Logger]` | Optional logger to use for debug output. If not provided, the module-level logger is used. | `None` |

Raises:

| Type | Description |
| --- | --- |
| `Error` | If establishing the connection or executing the SQL fails. |
| `Exception` | Propagates any other exceptions raised by `InfdbClient`. |

## `get_db_engine(cfg: InfdbConfig, db_name: str = DEFAULT_DB_NAME, logger: Optional[logging.Logger] = None)`

Return a SQLAlchemy Engine using InfdbClient (URL building is centralized).

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `cfg` | `InfdbConfig` | `InfdbConfig` instance used to resolve database connection parameters. | *required* |
| `db_name` | `str` | Name of the database to connect to. Defaults to `DEFAULT_DB_NAME`. | `DEFAULT_DB_NAME` |
| `logger` | `Optional[Logger]` | Optional logger to use for diagnostics. If not provided, the module-level logger is used. | `None` |

Returns:

| Type | Description |
| --- | --- |
|  | A SQLAlchemy `Engine` connected to the configured database. |

Raises:

| Type | Description |
| --- | --- |
| `Error` | If establishing the underlying connection fails. |
| `Exception` | Propagates any other exceptions raised by `InfdbClient`. |

## `compute_signature(items: Iterable[str]) -> str`

Produce a stable signature string from an iterable of strings.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `items` | `Iterable[str]` | Iterable of strings to combine in order. | *required* |

Returns:

| Type | Description |
| --- | --- |
| `str` | A single string formed by joining `items` with a pipe (`|`) separator. |
