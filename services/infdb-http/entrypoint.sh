#!/bin/sh

# Set default credentials if not provided
USER=${BASIC_AUTH_USER:-user}
PASS=${BASIC_AUTH_PASSWORD:-password}

# Generate .htpasswd file
htpasswd -bc /etc/nginx/.htpasswd "$USER" "$PASS"

# Execute the CMD
exec "$@"
