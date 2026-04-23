#!/bin/bash

## Usage:
# Profile: bash tools.sh -p PROFILE AGS
# Single Tool: bash tools.sh -t TOOLNAME AGS

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