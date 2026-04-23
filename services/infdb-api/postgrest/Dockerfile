FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

WORKDIR /workspaces/pgrstwatch

# Copy the rest of the application code into the container
COPY workspaces/pgrstwatch/watch_and_update_postgrest_conf.py /workspaces/pgrstwatch/watch_and_update_postgrest_conf.py


COPY workspaces/pgrstwatch/pyproject.toml /workspaces/pgrstwatch/pyproject.toml

# not possible at build time when using infdb only as mount. requires infdb in PyPI.
# RUN uv sync

# Set the default command to run the application
#CMD ["echo","[pgrstwatch] starting", "&&", "uv","run","python","watch_and_update_postgrest_conf.py"]

CMD uv sync && echo "[pgrstwatch] starting" && uv run python watch_and_update_postgrest_conf.py
