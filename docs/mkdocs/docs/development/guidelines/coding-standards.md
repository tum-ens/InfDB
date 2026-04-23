# Coding Standards

## Purpose

The purpose of these coding guidelines is to establish a consistent, maintainable, and high-quality codebase for the InfDB project. By following these guidelines, we aim to:

- **Ensure Code Consistency**: Establish uniform coding practices across the project to make the codebase more readable and maintainable.
- **Improve Collaboration**: Enable developers to work together more effectively by following shared conventions and practices.
- **Reduce Technical Debt**: Prevent the accumulation of technical debt by enforcing best practices from the start.
- **Enhance Code Quality**: Produce robust, efficient, and secure code that meets the specific needs of energy infrastructure digital twins.
- **Facilitate Onboarding**: Help new developers quickly understand the project structure and coding expectations.
- **Support Domain-Specific Requirements**: Address the unique challenges of energy system modeling, time-series data handling, and geospatial analysis.

These guidelines are not meant to be restrictive but rather to provide a framework that promotes code quality while allowing for innovation and creativity in solving complex energy domain problems.

## General

- Use **Python 3.12+** for development
- Follow **PEP 8** for Python code style 
- Use **4 spaces** for indentation in Python files
- Use **meaningful variable and function names** that describe their purpose
- Keep functions and methods **small and focused** on a single responsibility
- Write **docstrings** for all functions, classes, and modules
- Always include docstrings in Google style

## Python Specific

- Use **type hints** for all function parameters and return values
- Use **SQLModel** for data validation and database interactions
- Follow the **dependency injection** pattern using FastAPI's dependency system
- Use **async/await** for I/O-bound operations
- Implement proper **error handling** with custom exception classes
- Separate **business logic** from **API handlers**

## Automated Formatting

- Use `ruff format` for automatic code format testing:
  ```bash
  pip install uv
  ruff check .
  ```
- Use `ruff check` for linting:
  ```bash
  pip install uv
  ruff format --check .
  ```

## Folders & Files

- Use `snake_case` when creating them if they are too long

## Variables

### Rules
- **Naming:** Use `snake_case` for variables; use **`UPPER_SNAKE_CASE`** for constants.
- **Placement:** Define constants at the top of the module.
- **Clarity:** Prefer descriptive names (e.g., `min_rebuild_gap_seconds` over `gap`).
- **Types:** Add type annotations when they improve clarity or tooling.
- **Booleans:** Name so they read naturally (e.g., `schema_changed`, `enough_time_elapsed`).
- **Environment values:** Centralize reads of environment variables; never hardcode secrets.

### Example
```python
import os
import pathlib

OUTPUT_PATH = pathlib.Path("out.yml")
FALLBACK_EPSG = 25832

min_rebuild_gap_seconds: float = 3.0
schema_changed: bool = False
port: int = int(os.getenv("PORT", "5432") or "5432")
```

## Functions

### Rules
- **Single responsibility:** Keep functions small and single-purpose.
- **Typing:** Annotate parameters and return types (e.g., `Optional[str]`, `int`).
- **Docstrings:** Provide a one-line summary, then `Args` / `Returns` / `Raises` (Google style).
- **Validation (optional):** Validate inputs early and fail fast on misuse.

### Example
```python
from __future__ import annotations

import os
import sys
from typing import Optional


def env(name: str, default: Optional[str] = None, *, required: bool = False) -> Optional[str]:
    """Read an environment variable with default/required semantics.

    Args:
        name: Variable name.
        default: Fallback value if the variable is unset.
        required: If True, exit the program when the variable is missing or empty.

    Returns:
        The environment variable's value, or `default` if not set.

    Raises:
        SystemExit: If `required` is True and the variable is missing or empty.
    """
    val = os.getenv(name, default)
    if required and (val is None or val == ""):
        print(f"[ERR] missing required env: {name}", file=sys.stderr)
        sys.exit(2)
    return val
```

## Type Annotations

- Use type hints for all function parameters and return values:
  ```python
  def get_raster_center(building_id: int, resolution: int) -> dict:
      # Function implementation
  ```
- Use `Optional[Type]` for parameters that can be None.
- Use `Union[Type1, Type2]` for parameters that can be multiple types.
- Use `List[Type]`, `Dict[KeyType, ValueType]`, etc. for container types.
