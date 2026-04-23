FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

WORKDIR /workspaces/choose-a-name

# COPY requiremets into the container
COPY pyproject.toml pyproject.toml
# COPY uv.lock uv.lock

# Copy the source code into the container
COPY src src
COPY sql sql
COPY main.py main.py

# Run main.py with uv and environment defined in pyproject.toml
CMD ["uv", "run", "python", "main.py"]