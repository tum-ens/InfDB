FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

WORKDIR /app

# COPY requiremets into the container
COPY pyproject.toml /app/pyproject.toml
# COPY uv.lock /app/uv.lock

## Install infdb package in editable mode
# COPY infdb_package /app/infdb_package
# RUN uv pip install -e /app/infdb_package

# Copy the source code into the container
COPY src /app/src
COPY sql /app/sql
COPY main.py /app/main.py

# Run main.py with uv and environment defined in pyproject.toml
CMD ["uv", "run", "python", "main.py"]
