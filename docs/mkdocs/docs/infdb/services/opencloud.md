---
icon: material/cloud
---
# OpenCloud :material-cloud:

OpenCloud is a self-hosted file share platform for managing data imports and exports.

## Configuration

The configuration is managed via environment variables:

```bash title=".env"
# ==============================================================================
# SERVICE ACTIVATION
# ==============================================================================
# Select profiles to activate
COMPOSE_PROFILES=...,opencloud,...  # (1)

# ==============================================================================
# OPENCLOUD SERVICE
# ==============================================================================
# Profile: opencloud

# Port on which the OpenCloud is available on the host machine
SERVICES_OPENCLOUD_EXPOSED_PORT=80 # (2)
```

1.  **Activate service**: The `opencloud` profile must be included to activate the OpenCloud service.
2.  **Port**: The port on which the OpenCloud is available.

## Access

If you activate the service, it should be available on the default port `SERVICES_OPENCLOUD_EXPOSED_PORT=80` via your browser:

=== "Local"
    http://localhost:80

=== "Remote"
    http://IP-ADDRESS-OF-HOST:80
