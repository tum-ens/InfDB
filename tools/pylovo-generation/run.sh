#!/bin/bash
set -e

# echo "Starting docker compose..."
docker compose -f "$(dirname "$0")/compose.yml" run --rm --build pylovo-generation