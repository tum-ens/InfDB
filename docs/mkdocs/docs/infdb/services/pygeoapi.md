---
icon: material/earth
---
# pygeoapi :material-earth:

The pygeoapi service provides a standards-based interface for sharing spatial data with external GIS tools and web applications.

## Configuration

The configuration is managed via environment variables:

```bash title=".env"
# ==============================================================================
# SERVICE ACTIVATION
# ==============================================================================
# Select profiles to activate
COMPOSE_PROFILES=...,pygeoapi,...  # (1)

# ==============================================================================
# PYGEOAPI SERVICE
# ==============================================================================
# Profile: pygeoapi

# Port on which the pygeoapi is available on the host machine
SERVICES_PYGEOAPI_EXPOSED_PORT=5000 # (2)
```

1.  **Activate service**: The `pygeoapi` profile must be included to activate the pygeoapi service.
2.  **Port**: The port on which the pygeoapi is available.

## Access

If you activate the service, it should be available on the default port `SERVICES_PYGEOAPI_EXPOSED_PORT=5000` via your browser:

=== "Local"
    http://localhost:5000

=== "Remote"
    http://IP-ADDRESS-OF-HOST:5000
