# Client

## `InfdbClient`

Thin Postgres client backed by psycopg2 with a SQLAlchemy engine helper.

### `__init__(infdb_config: InfdbConfig, log: logging.Logger, db_name: str = 'postgres') -> None`

Initialize the client and open a connection.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `infdb_config` | `InfdbConfig` | Configuration provider for database parameters. | *required* |
| `log` | `Logger` | Logger instance to use for diagnostics. | *required* |
| `db_name` | `str` | Database name to connect to (defaults to "postgres"). | `'postgres'` |

Raises:

| Type | Description |
| --- | --- |
| `OperationalError` | If the connection cannot be established. |

### `__enter__() -> InfdbClient`

Enter context manager (returns self).

### `__exit__(exc_type, exc, tb) -> None`

Exit context manager and close resources.

### `close() -> None`

Close cursor and connection, ignoring close-time exceptions.

### `__del__() -> None`

Best-effort resource cleanup on GC.

### `__str__() -> str`

Human-readable description of the client.

### `execute_query(query: str, params: ParamsTuple = None) -> List[Row]`

Execute SQL and return fetched rows; return [] for non-SELECT statements.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `query` | `str` | SQL query to execute. | *required* |
| `params` | `ParamsTuple` | Optional positional parameters for the query. | `None` |

Returns:

| Type | Description |
| --- | --- |
| `List[Row]` | A list of rows for SELECT-like statements; empty list for statements without a result set. |

### `execute_sql_files(sql_dir: str, file_list: Optional[Sequence[str]] = None, format_params: Optional[Dict[str, Any]] = None)`

Execute a set of .sql files in lexicographic order by default.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `sql_dir` | `str` | Directory containing SQL files. | *required* |
| `file_list` | `Optional[Sequence[str]]` | Optional explicit list of filenames to execute (in given order). | `None` |
| `format_params` | `Optional[Dict[str, Any]]` | Optional dict for Python str.format substitutions. | `None` |

Raises:

| Type | Description |
| --- | --- |
| `FileNotFoundError` | If the directory or a specified file does not exist. |
| `Exception` | Re-raises any execution error after rolling back. |

### `execute_sql_file(file_path: str, format_params: Optional[Dict[str, Any]] = None) -> None`

Execute a single SQL file by delegating to execute\_sql\_files.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `file_path` | `str` | Absolute or relative path to the SQL file. | *required* |
| `format_params` | `Optional[Dict[str, Any]]` | Optional dict for Python str.format substitutions. | `None` |

### `get_db_engine()`

Create and return a SQLAlchemy engine for the target DB.

Returns:

| Type | Description |
| --- | --- |
|  | A SQLAlchemy Engine connected to the configured database. |

### `get_db_params() -> DBParams`

Return a shallow copy of the resolved DB parameters.

Returns:

| Type | Description |
| --- | --- |
| `DBParams` | A dictionary of database parameters. |
