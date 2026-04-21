#!/bin/bash
# Run this script from the same directory, e.g. bash run.sh [AGS]
# Small wrapper script to export required environment variables into shell
# all arguments are passed to docker compose
# e.g.: bash run.sh 9185149, bash run.sh (interactive)
set -e

echo "Loading environment variables from .env file..."
set -a
[ -f $(dirname "$0")/../../.env ] && . $(dirname "$0")/../../.env
set +a

PARAM="${1:-$AGS}"
OPTIONS="${2:-}"

echo "Starting docker compose..."
export AGS="$PARAM"

docker compose -f "$(dirname "$0")/compose.yml" run --rm --build pylovo-generation