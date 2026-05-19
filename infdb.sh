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
    read -r -a selected_profiles <<< "$(read_profiles)"
    echo "Selected profiles: ${selected_profiles[*]}"

    setup_services "${selected_profiles[@]}"
    generate_compose "${selected_profiles[@]}"

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
    docker compose down
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

read_profiles() {
    if [[ -z "${COMPOSE_PROFILES:-}" ]]; then
        echo "Error: COMPOSE_PROFILES is not set in .env" >&2
        exit 1
    fi

    # Remove spaces, convert comma separated values to array
    local normalized
    normalized=$(echo "$COMPOSE_PROFILES" | tr -d '[:space:]')

    IFS=',' read -r -a profiles <<< "$normalized"

    if [[ ${#profiles[@]} -eq 0 ]]; then
        echo "Error: No valid profiles in COMPOSE_PROFILES" >&2
        exit 1
    fi

    echo "${profiles[@]}"
}

get_profile_paths() {
    case "$1" in
        db)
            echo "services/infdb-db/compose.yml"
            ;;
        admin)
            echo "services/pgadmin/compose.yml"
            ;;
        api)
            cat <<EOF
services/infdb-api/fastapi/compose.yml
services/infdb-api/pygeoapi/compose.yml
services/infdb-api/postgrest/compose.yml
EOF
            ;;
        notebook)
            echo "services/jupyter/compose.yml"
            ;;
        qwc)
            echo "services/infdb-qwc/compose.yml"
            ;;
        lizmap)
            echo "services/infdb-lizmap/docker-compose.yml"
            ;;
        opencloud)
            echo "services/infdb-opencloud/docker-compose.yml"
            ;;
        *)
            echo "Error: Unknown profile '$1'" >&2
            exit 1
            ;;
    esac
}

# Setup before initialization of services that require it.
setup_services() {
    local profiles=("$@")
    
    for profile in "${profiles[@]}"; do
        case "$profile" in
            lizmap)
                configure_lizmap
                ;;
            # You can easily add other services that require configurations here:
            # opencloud) configure_opencloud ;;
            # qwc) configure_qwc ;;
            # ...
        esac
    done
}

generate_compose() {
    local output_file="compose.yml"

    # Explicitly remove existing compose file
    if [[ -f "$output_file" || -L "$output_file" ]]; then
        echo "=== Removing existing $output_file ==="
        rm -f "$output_file"
    fi

    local profiles=("$@")

    echo "=== Generating $output_file from COMPOSE_PROFILES: $COMPOSE_PROFILES ==="

    declare -A seen
    local paths=()

    for profile in "${profiles[@]}"; do

        while IFS= read -r path; do
            [[ -z "$path" ]] && continue

            if [[ -z "${seen[$path]}" ]]; then
                if [[ ! -f "$path" ]]; then
                    echo "Error: Missing compose file: $path" >&2
                    exit 1
                fi

                paths+=("$path")
                seen["$path"]=1
            fi
        done < <(get_profile_paths "$profile")
    done

    {
        echo "name: \${BASE_NAME}"
        echo
        echo "include:"
        for p in "${paths[@]}"; do
            echo "  - path: $p"
        done
        echo
        echo "networks:"
        echo "  infdb_network:"
        echo "    name: infdb-\${BASE_NAME}_network"
        echo "    driver: bridge"
    } > "$output_file"

    echo "=== Generated $output_file with ${#paths[@]} includes ==="
}

configure_lizmap() {
    if [ ! -d "services/infdb-lizmap/lizmap" ]; then
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
