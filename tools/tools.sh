#!/bin/bash

# ----------------------------------------------------------------------
# InfDB Tools User Interface for Single AGS
# Purpose:
#   Runs InfDB tools defined in tools/compose.yml either linked by Docker
#   Compose profile or as a single named service for single AGS. This gives 
#   users a single entrypoint for executing processing tools against in the 
#   InfDB tool framework without needing to know the underlying infrastructure behind.
#
# Usage:
#   bash tools.sh -p <profile> <ags> 
#   bash tools.sh -t <tool> <ags>
#
# Examples:
#   bash tools.sh -p linear 09780139    # Run the "linear" profile for the AGS 09780139
#   bash tools.sh -t ro-heat 09780139   # Run the "ro-heat" tool for the AGS 09780139
#
# The script loads variables from the repository .env file and the local
# tools.env file before starting the requested Compose workload.
# ----------------------------------------------------------------------

echo "Loading environment variables from infDB .env file..."
set -a
[ -f $(dirname "$0")/../.env ] && . $(dirname "$0")/../.env
set +a

echo "Loading environment variables from local tools.env file..."
set -a
[ -f $(dirname "$0")/tools.env ] && . $(dirname "$0")/tools.env
set +a

usage() {
    echo "Usage: $0 (-p <profile> | -t <tool>)"
    echo "  -p <profile>  Run profile (e.g., linear) AGS"
    echo "  -t <tool>     Run tool (e.g., ro-heat) AGS"
    exit 1
}

# Check for required parameters
if [[ $# -ne 3 ]]; then
    usage
fi

# Extract NAME and additional parameters
NAME="$2"
AGS="$3"
OPTIONS="$4"

# Use the shared infdb network for all tool runs
export INFDB_NETWORK="${INFDB_NETWORK:-infdb-${BASE_NAME}_network}"

# Get 
PROJECT="infdb_${AGS}"
export AGS="$AGS"

case "$1" in
    -p)        
        echo "Running profile: $NAME"

        # Start the specified profile
        docker compose -f "$(dirname "$0")/compose.yml" \
            -p "$PROJECT" \
            --profile "$NAME" up\
            --remove-orphans
        
        # Stop and remove containers, networks, images, and volumes created by up
        docker compose -f "$(dirname "$0")/compose.yml" \
            -p "$PROJECT" \
            --profile "$NAME" down\
            --volumes --remove-orphans  # --rmi all
        ;;
    -t)
        echo "Running tool: $NAME"
        
        # Start the specified tool without dependencies
        docker compose -f "$(dirname "$0")/compose.yml" -p "$PROJECT" up --no-deps --remove-orphans $OPTIONS "$NAME"

        # Stop and remove containers, networks, images, and volumes created by up
        docker compose -f "$(dirname "$0")/compose.yml" -p "$PROJECT" down --volumes --remove-orphans "$NAME"
        ;;
    *)
        # Explanin usage if the first argument is not -p or -t
        usage
        ;;
esac