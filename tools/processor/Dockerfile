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
#ENV PYTHONPATH=/tools/processor/

## Run python scripts with uv
# COPY requiremets into the container
COPY pyproject.toml /tools/processor/pyproject.toml
#COPY config-processor.yml /tools/processor/config-processor.yml
RUN uv sync

# Copy the source code into the container
#OPY src /tools/processor/src

# Run main.py with uv and environment defined in pyproject.toml
CMD ["uv", "run", "python", "main.py"]
