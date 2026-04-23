FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

WORKDIR /workspaces/pygeowatch

# Copy application code into the container
COPY workspaces/pygeowatch/watch_and_generate_pygeoapi_config.py /workspaces/pygeowatch/watch_and_generate_pygeoapi_config.py

COPY workspaces/pygeowatch/pyproject.toml /workspaces/pygeowatch/pyproject.toml

# not possible at build time when using infdb only as mount. requires infdb in PyPI.
# RUN uv sync


# Set the default command to run the application
#CMD echo "[pygeowatch] starting" && uv run python watch_and_generate_pygeoapi_config.py

CMD uv sync && echo "[pygeowatch] starting" && uv run python watch_and_generate_pygeoapi_config.py
