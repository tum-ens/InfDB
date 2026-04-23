---
icon: material/api
---
# PostgREST :material-api:

The PostgREST service provides an automatic REST API for reading tables and running queries without building custom code.

## Configuration

The configuration is managed via environment variables:

```bash title=".env"
# ==============================================================================
# SERVICE ACTIVATION
# ==============================================================================
# Select profiles to activate
COMPOSE_PROFILES=...,postgrest,...  # (1)
COMPOSE_PROFILES=...,swagger,...  # (2)

# ==============================================================================
# POSTGREST SERVICE
# ==============================================================================
# Profile: postgrest

# Port on which the PostgREST is available on the host machine
SERVICES_POSTGREST_EXPOSED_PORT=3000 # (3)
SERVICES_SWAGGER_EXPOSED_PORT=8080 # (4)
```

1.  **Activate service**: The `postgrest` profile must be included to activate the PostgREST service.
2.  **Activate Swagger**: The `swagger` profile must be included to activate the Swagger UI service.
3.  **PostgREST Port**: The port on which the PostgREST is available.
4.  **Swagger Port**: The port on which the Swagger UI is available.

## Access

If you activate the service, it should be available on the default port `SERVICES_POSTGREST_EXPOSED_PORT=3000` via your browser:

=== "Local"
    http://localhost:3000

=== "Remote"
    http://IP-ADDRESS-OF-HOST:3000
