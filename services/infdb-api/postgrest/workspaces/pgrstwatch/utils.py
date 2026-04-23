import os
import logging
import tempfile
from typing import Optional, cast, Iterable, Any #, List,

# ============================== Constants ==============================

LOGGER_NAME: str = "infdb.utils"
DEFAULT_DB_NAME: str = "postgres"
FILE_ENCODING: str = "utf-8"

# Module-level logger
log = logging.getLogger(LOGGER_NAME)

def read_text(input_path: str) -> str:
    """
    Reads a text file; returns empty string if it does not exist.

    Args:
        input_path: Path to the file to read.

    Returns:
        The file contents as a string. If the file does not exist, returns an
            empty string.

    Raises:
        OSError: For IO errors other than `FileNotFoundError` (e.g., permission
            denied).
    """
    try:
        with open(input_path, "r", encoding=FILE_ENCODING) as f:
            return f.read()
    except FileNotFoundError:
        return ""

   
def read_env(var_name: str, default: Optional[str] = None, required: bool = False) -> str:
    """
    Reads an environment variable with optional default and required check.

    Args:
        var_name: Name of the environment variable to read.
        default: Value to return if the environment variable is not set.
        required: If True, treat a missing or empty value as an error and exit.

    Returns:
        The environment variable value, or `default` if it is not set. If `required`
            is True and the value is missing/empty, the function does not return.

    Raises:
        SystemExit: Exits with status code 2 if `required` is True and the variable
            is missing or empty.
    """
    v = os.getenv(var_name)
    is_missing = (v is None) or (v == "")
    if required and is_missing:
        log.error("Missing required env variable: %s", var_name)
        raise SystemExit(2)
    if is_missing:
        return default if default is not None else ""
    return cast(str, v)


def build_dsn_from_env(
    user_var: str,
    pwd_var: str,
    db_var: str,
    host_var: str,
    port_var: int,
) -> str:
    """
    Builds a PostgreSQL DSN string from common environment variables.

    Args:
        user_var: Database username.
        pwd_var: Database password.
        db_var: Database name.
        host_var: Database host.
        port_var: Database port.

    Returns:
        A PostgreSQL connection URL (DSN) in the form:
            `postgresql://<user>:<password>@<host>:<port>/<db>`.
    """
    return f"postgresql://{user_var}:{pwd_var}@{host_var}:{port_var}/{db_var}"

# ============================== Misc helpers ==============================


def compute_signature(items: Iterable[str]) -> str:
    """
    Produces a stable signature string from an iterable of strings.

    Args:
        items: Iterable of strings to combine in order.

    Returns:
        A single string formed by joining `items` with a pipe (`|`) separator.
    """
    return "|".join(items)


def _atomic_write(
    binary: bool, data: Any, output_path: str, file_mode: str | None = None, dir_mode: str | None = None
) -> str:
    """
    Internal: writes text/bytes atomically and optionally set chmods.

    Args:
        binary: If True, write `data` as bytes using binary mode (`wb`).
            If False, write `str(data)` using text mode (`w`) with `FILE_ENCODING`.
        data: The content to write. Must be `bytes` when `binary` is True; otherwise
            it will be coerced to `str`.
        output_path: Destination file path (absolute or relative). Parent directories
            will be created if needed.
        file_mode: Optional file permission mode (octal string, e.g. `"644"` or `"600"`).
        dir_mode: Optional directory permission mode (octal string) to apply to the
            destination directory.

    Returns:
        The absolute path of the written file.

    Raises:
        ValueError: If `output_path` is empty.
        OSError: If writing, syncing, replacing, or chmod operations fail (except
            directory chmod failures, which are logged and ignored).
    """
    if not output_path:
        raise ValueError("output_path must be a non-empty string")

    path = output_path if os.path.isabs(output_path) else os.path.abspath(output_path)
    out_dir = os.path.dirname(path)
    os.makedirs(out_dir, exist_ok=True)

    mode = "wb" if binary else "w"
    with tempfile.NamedTemporaryFile(
        mode, delete=False, dir=out_dir, suffix=".tmp", encoding=None if binary else FILE_ENCODING
    ) as tmp:
        if binary:
            tmp.write(data)  # bytes
        else:
            tmp.write(str(data))  # text
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_name = tmp.name
    os.replace(tmp_name, path)

    if file_mode:
        os.chmod(path, int(file_mode, 8))
    if dir_mode:
        try:
            os.chmod(out_dir, int(dir_mode, 8))
        except Exception as exc:
            log.exception("Exception occurred during _atomic_write(): %s", exc)

    return path


def atomic_write_text(text: str, output_path: str, file_mode: str | None = None, dir_mode: str | None = None) -> str:
    """
    Atomically writes text to a file. Optionally apply chmod to file/dir.

    Args:
        text: Text content to write.
        output_path: Destination file path (absolute or relative). Parent directories
            will be created if needed.
        file_mode: Optional file permission mode (octal string, e.g. `"644"` or `"600"`).
        dir_mode: Optional directory permission mode (octal string) to apply to the
            destination directory.

    Returns:
        The absolute path of the written file.

    Raises:
        ValueError: If `output_path` is empty.
        OSError: If writing, syncing, or replacing the file fails (and potentially
            if applying `file_mode` fails).
    """
    return _atomic_write(binary=False, data=text, output_path=output_path, file_mode=file_mode, dir_mode=dir_mode)
