# Logger

## `InfdbLogger`

Console + file logging with a multiprocessing-safe queue listener.

### `__init__(log_path: str, level: str = 'INFO', cleanup: bool = False) -> None`

Initialize root logger, handlers, and a QueueListener.

Parameters:

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `log_path` | `str` | Path to the log file to write. | *required* |
| `level` | `str` | Logging level name (e.g., 'INFO', 'DEBUG'). | `'INFO'` |
| `cleanup` | `bool` | If True, remove any existing log file at `log_path` before starting. | `False` |

### `stop()`

Flush and stop the QueueListener.

### `setup_worker_logger() -> logging.Logger`

Create a logger for worker processes that forwards to the queue.

Returns:

| Type | Description |
| --- | --- |
| `Logger` | A logger configured with a QueueHandler that sends records to the root listener. |
