#!/bin/bash
# Run this script from the same directory, e.g. bash run.sh up
# Small wrapper script to export required environment variables into shell
# all arguments are passed to docker compose
# e.g.: bash run.sh up, bash run.sh up --build, bash run.sh down, bash run.sh stop, ...
set -e

# Load environment variables from .env file
set -a
[ -f $(dirname "$0")/../../.env ] && . $(dirname "$0")/../../.env
set +a

docker compose -f "$(dirname "$0")/compose.yml" "$@"
