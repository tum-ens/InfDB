#!/bin/bash
set -e

echo "Loading environment variables from .env file..."
set -a
[ -f $(dirname "$0")/../../.env ] && . $(dirname "$0")/../../.env
set +a

echo "Starting docker compose..."
docker compose -f "$(dirname "$0")/compose.yml" up --build