FROM python:latest

WORKDIR /tools/processor/

## Install uv on Ubuntu
# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Download the latest uv installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# COPY requiremets into the container
COPY pyproject.toml /tools/processor/pyproject.toml

## Install venv with uv
RUN uv sync

# Run main.py with uv and environment defined in pyproject.toml
#CMD ["uv", "run", "python", "main.py"]
