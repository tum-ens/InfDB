import logging
import os
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

import psycopg2
import sqlalchemy
from psycopg2 import OperationalError
import pandas as pd

from .config import InfdbConfig

# ============================== Constants ==============================
DB_URL_TEMPLATE: str = "postgresql://{user}:{password}@{host}:{port}/{db}"


# ============================== Types ==================================

Row = Tuple[Any, ...]
ParamsTuple = Optional[Tuple[Any, ...]]
DBParams = Dict[str, Any]


class InfdbClient:
    """Thin Postgres client backed by psycopg2 with a SQLAlchemy engine helper."""

    def __init__(self, infdb_config: InfdbConfig, log: logging.Logger, db_name: str = "postgres") -> None:
        """Initializes the client and opens a connection.

        Args:
            infdb_config: Configuration provider for database parameters.
            log: Logger instance to use for diagnostics.
            db_name: Database name to connect to (defaults to "postgres").

        Raises:
            OperationalError: If the connection cannot be established.
        """
        self.log = log
        self.db_params: DBParams = infdb_config.get_db_parameters()
        try:
            self.conn = psycopg2.connect(
                host=self.db_params.get("host"),
                port=self.db_params.get("exposed_port"),
                database=self.db_params.get("db"),
                user=self.db_params.get("user"),
                password=self.db_params.get("password"),
            )
            self.conn.autocommit = True
            self.cur = self.conn.cursor()
        except OperationalError as err:
            self.log.warning(
                "Connecting to %s was not successful. Ensure SSH/port mapping is established.",
                self.db_params,
            )
            raise err
        self.log.debug("InfdbClient connected to %s", self.db_params)

    # -------------------------- Context Manager --------------------------

    def __enter__(self) -> "InfdbClient":
        """Enters the context manager (returns self)."""
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Exits the context manager and closes resources."""
        self.close()

    # -------------------------- Lifecycle --------------------------------

    def close(self) -> None:
        """Closes the cursor and connection, ignoring close-time exceptions."""
        try:
            if getattr(self, "cur", None):
                self.cur.close()
            if getattr(self, "conn", None):
                self.conn.close()
        except Exception as exc:
            # Intentionally swallow exceptions on cleanup to preserve current behavior.
            self.log.exception("Exception occurred during close(): %s", exc)

    def __del__(self) -> None:
        """Performs best-effort resource cleanup on GC."""
        self.close()

    def __str__(self) -> str:  # pragma: no cover - human-readable aid
        """Returns a human-readable description of the client."""
        return f"InfdbClient connected to {self.db_params}"

    # --------------------------- Operations ------------------------------

    def execute_query(self, query: str, params: ParamsTuple = None) -> List[Row]:
        """Executes SQL and returns fetched rows; returns [] for non-SELECT statements.

        Args:
            query: SQL query to execute.
            params: Optional positional parameters for the query.

        Returns:
            A list of rows for SELECT-like statements; empty list for statements without a result set.
        """
        self.cur.execute(query, params)
        self.log.debug("Executed query: %s with params: %s", query, params)
        if self.cur.description is None:
            return []
        return self.cur.fetchall()

    def execute_sql_files(
        self,
        sql_dir: str,
        file_list: Optional[Sequence[str]] = None,
        format_params: Optional[Dict[str, Any]] = None,
    ):
        """Executes a set of .sql files in lexicographic order by default.

        Args:
            sql_dir: Directory containing SQL files.
            file_list: Optional explicit list of filenames to execute (in given order).
            format_params: Optional dict for Python str.format substitutions.

        Raises:
            FileNotFoundError: If the directory or a specified file does not exist.
            Exception: Re-raises any execution error after rolling back.
        """
        if not os.path.isdir(sql_dir):
            raise FileNotFoundError(f"SQL directory not found: {sql_dir}")

        files_to_run: Sequence[str]
        if file_list is None:
            files_to_run = sorted(f for f in os.listdir(sql_dir) if f.endswith(".sql"))
        else:
            files_to_run = file_list

        total_files = len(files_to_run)
        self.log.info("Executing %d SQL file(s)", total_files)

        for file_name in files_to_run:
            path = os.path.join(sql_dir, file_name)
            if not os.path.isfile(path):
                raise FileNotFoundError(f"SQL file not found: {path}")

            self.log.info("Executing SQL file: %s", path)
            started_at = time.time()
            try:
                with open(path, "r", encoding="utf-8") as f:
                    sql_content = f.read()

                if not sql_content.strip():
                    self.log.warning("File %s is empty. Skipping.", file_name)
                    continue

                if format_params:
                    sql_content = sql_content.format(**format_params)

                self.cur.execute(sql_content)
                self.conn.commit()
                self.log.info("Success: %s (%.2fs)", file_name, time.time() - started_at)
            except Exception as exc:
                self.conn.rollback()
                self.log.error("Failed: %s (%s)", file_name, exc)
                raise

    def execute_sql_file(self, file_path: str, format_params: Optional[Dict[str, Any]] = None) -> None:
        """Executes a single SQL file by delegating to execute_sql_files.

        Args:
            file_path: Absolute or relative path to the SQL file.
            format_params: Optional dict for Python str.format substitutions.
        """
        self.execute_sql_files(
            os.path.dirname(file_path),
            [os.path.basename(file_path)],
            format_params=format_params,
        )

    def get_db_engine(self):
        """Creates and returns a SQLAlchemy engine for the target DB.

        Returns:
            A SQLAlchemy Engine connected to the configured database.
        """
        db_url = DB_URL_TEMPLATE.format(
            user=self.db_params.get("user"),
            password=self.db_params.get("password"),
            host=self.db_params.get("host"),
            port=self.db_params.get("exposed_port"),
            db=self.db_params.get("db"),
        )
        return sqlalchemy.create_engine(db_url)

    def get_db_params(self) -> DBParams:
        """Returns a shallow copy of the resolved DB parameters.

        Returns:
            A dictionary of database parameters.
        """
        return dict(self.db_params)
    
    def get_pandas(self, sql: str, format_params: Optional[Dict[str, Any]] = None) -> Any:
        """Helper method to read SQL query results into a pandas DataFrame."""
        if format_params:
            sql = sql.format(**format_params)
        
        return pd.read_sql(sql, self.get_db_engine())

    def get_pandas_sqlfile(self, path: str, format_params: Optional[Dict[str, Any]] = None) -> Any:
        """Helper method to read SQL query files results into a pandas DataFrame."""
        with open(path, "r", encoding="utf-8") as file:
            sql_content = file.read()
        
        return self.get_pandas(sql_content, format_params=format_params)