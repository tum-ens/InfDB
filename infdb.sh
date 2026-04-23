#!/usr/bin/env bash
set -e

# ----------------------------------------------------------------------
# infDB command script
# Usage:
#   ./infdb.sh start [docker compose args]
#   ./infdb.sh import [docker compose args]
#   ./infdb.sh stop
#   ./infdb.sh remove
# ----------------------------------------------------------------------

# Ensure relative path works
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_usage() {
    cat <<'EOF'
Usage:
  ./infdb.sh start [docker compose args]
  ./infdb.sh import [docker compose args]
  ./infdb.sh stop
  ./infdb.sh remove

Examples:
  ./infdb.sh start -d
  ./infdb.sh import --build
  ./infdb.sh stop
  ./infdb.sh remove
EOF
}

ensure_from_template() {
    local target_file="$1"
    local template_file="$2"

    if [ ! -f "$target_file" ]; then
        echo "=== Creating $target_file from template ==="
        cp "$template_file" "$target_file"
        echo "=== $target_file file created. Please review and customize it as needed. ==="
    fi
}

cmd_start() {
    configure_lizmap

    echo "=== Pull latest docker images ==="
    docker compose pull --ignore-buildable

    echo "=== Starting infDB ==="
    if [ $# -eq 0 ]; then
        docker compose up --pull never -d
    elif [ "$1" = "" ]; then
        docker compose up --pull never
    else
        docker compose up --pull never "$@"
    fi

    echo "=== Successfully started InfDB. ==="
}

cmd_import() {
    ensure_from_template "configs/config-infdb-import.yml" "configs/config-infdb-import.yml.template"
    echo "=== Importing data ==="
    docker compose --profile "import" up "$@"
}

cmd_stop() {
    echo "=== Stopping infDB ==="
    docker compose --profile "*" down
    echo "Successfully stopped all InfDB services."
}

cmd_remove() {
    echo "=== Removing service $1 including data  ==="
    docker compose --profile "$1" down -v --remove-orphans
    if { [[ "$1" == *"lizmap"* ]] || [[ "$1" == *"*"* ]]; }; then
        cd services/infdb-lizmap
        ./configure.sh clean
        cd "$SCRIPT_DIR"
    fi
}

configure_lizmap() {
    echo ${COMPOSE_PROFILES}
    if [[ ":${COMPOSE_PROFILES}:" == *"lizmap"* ]] && [ ! -d "services/infdb-lizmap/lizmap" ]; then
        echo "=== Configuring lizmap ==="
        cd services/infdb-lizmap
        ./configure.sh configure
        chmod +x lizmap/etc/postgres.init.d/init-lizmap-db.sh
        cd "$SCRIPT_DIR"
    fi
}

if [ $# -lt 1 ]; then
    print_usage
    exit 1
fi

ensure_from_template ".env" ".env.template"

# Load environment variables from .env if it exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -o allexport
    source "$SCRIPT_DIR/.env"
    set +o allexport
fi

export UID GID="$(id -g)"

# Set default platform for Docker to linux/amd64 only on Apple Silicon
if [[ "$(uname -s)" == "Darwin" ]] && [[ "$(uname -m)" == "arm64" ]]; then
    export DOCKER_DEFAULT_PLATFORM=linux/amd64
fi

COMMAND="$1"
shift
case "$COMMAND" in
    start)
        cmd_start "$@"
        ;;
    import)
        cmd_import "$@"
        ;;
    stop)
        cmd_stop "$@"
        ;;
    remove)
        cmd_remove "$@"
        ;;
    -h|--help|help)
        print_usage
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo
        print_usage
        exit 1
        ;;
esac
