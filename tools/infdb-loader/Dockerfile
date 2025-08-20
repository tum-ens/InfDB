FROM 3dcitydb/citydb-tool

WORKDIR /app

## Install uv on Ubuntu
# The installer requires curl (and certificates) to download the release archive
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Install aria2 for downloading lod2 of bavaria
RUN apt-get install -y aria2

# Download the latest uv installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

## Run python scripts with uv
# COPY requiremets into the container
COPY pyproject.toml /app/pyproject.toml
#COPY config-loader.yml /app/config-loader.yml
RUN uv sync

# Copy the source code into the container
COPY src /app/src
COPY main.py /app/main.py

# Reset entrypoint to the default because of citydb-tool image
ENTRYPOINT []

# Run main.py with uv and environment defined in pyproject.toml
CMD [ "uv", "run", "python", "main.py"]
