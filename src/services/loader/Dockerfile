FROM ubuntu:latest

WORKDIR /app

## Install uv on Ubuntu
# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"


## Run python scripts with uv
# COPY requiremets into the container
COPY src/services/loader/pyproject.toml /app/pyproject.toml

# Copy the source code into the container
COPY src /app/src

# Run main.py with uv and environment defined in pyproject.toml
CMD ["uv", "run", "python", "-m", "src.services.loader.main"]



#FROM python:3.12
#
#RUN apk add --no-cache \
#    gdal-dev \
#    aria2 \
#    python3-dev \
#    py3-pip \
#    build-base \
#    geos-dev \
#    proj-dev
#
#WORKDIR /app
#
#COPY src/services/loader/requirements.txt requirements.txt
#RUN pip install --upgrade pip
#RUN pip install --no-cache-dir -r requirements.txt
#
#
#CMD ["python", "-u", "-m", "src.services.loader.main"]
