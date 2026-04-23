---
icon: material/api
---
# FastAPI :material-api:

The InfDB platform provides a FastAPI service for secure access to data through simple web requests (e.g., city information, weather data).

## Configuration

The configuration is managed via environment variables:

```bash title=".env"
# ==============================================================================
# SERVICE ACTIVATION
# ==============================================================================
# Select profiles to activate
COMPOSE_PROFILES=...,api,...  # (1)

# ==============================================================================
# API Services
# ==============================================================================
# Profile: api

# Port on which the FastAPI is available on the host machine
SERVICES_FASTAPI_EXPOSED_PORT=8000 # (2)
```

1.  **Activate service**: The `api` profile must be included to activate the FastAPI service.
2.  **Port**: The port on which the FastAPI is available.

## Access

If you activate the service, it should be available on the default port `SERVICES_FASTAPI_EXPOSED_PORT=8000` via your browser:

=== "Local"
    http://localhost:8000

=== "Remote"
    http://IP-ADDRESS-OF-HOST:8000
