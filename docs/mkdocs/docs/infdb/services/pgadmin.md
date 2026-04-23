---
icon: material/monitor-dashboard
---
# pgAdmin :material-monitor-dashboard:

pgAdmin is a feature-rich, open-source platform for administering PostgreSQL databases. It includes a graphical interface for writing SQL queries, viewing data, and monitoring database performance. More information can be found on the official [Website](https://www.pgadmin.org/).

## Configuration

The configuration is managed via environment variables:

```bash title=".env"
# ==============================================================================
# SERVICE ACTIVATION
# ==============================================================================
# Select profiles to activate
COMPOSE_PROFILES=...,pgadmin,...  # (1)

# ==============================================================================
# PGADMIN SERVICE
# ==============================================================================
# Profile: pgadmin

# Port on which the pgAdmin is available on the host machine
SERVICES_PGADMIN_EXPOSED_PORT=5050 # (2)

# Default email and password to login to pgAdmin
SERVICES_PGADMIN_DEFAULT_EMAIL=admin@admin.com # (3)
SERVICES_PGADMIN_DEFAULT_PASSWORD=root # (4)
```

1.  **Activate service**: The `pgadmin` profile must be included to activate the pgAdmin service.
2.  **Port**: The port on which the pgAdmin is available.
3.  **Email**: Default email to login to pgAdmin.
4.  **Password**: Default password to login to pgAdmin.

## Access

If you activate the service, it should be available on the default port `SERVICES_PGADMIN_EXPOSED_PORT=5050` via your browser:

=== "Local"
    http://localhost:5050

=== "Remote"
    http://IP-ADDRESS-OF-HOST:5050
