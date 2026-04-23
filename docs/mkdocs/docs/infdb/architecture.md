---
icon: material/domain
---
# InfDB Architecture :material-domain:

The architecture of InfDB is designed to be modular, scalable, and flexible, allowing for easy integration of various data sources and tools. This architecture is implemented using Docker Compose to orchestrate multiple services, including the core database, data importers, and various processing tools.

![InfDB Architecture](infdb-architecture.png)

## Core Components

-   **Docker Compose**: The extensive `compose.yml` file controls all containerized services.
-   **Helper Scripts**: Bash scripts (`infdb-start.sh`, `infdb-stop.sh`, etc.) simplify common management tasks.
-   **Configuration**:
    -   `.env`: Controls global settings like credentials, ports, and paths.
    -   `config-infdb-import.yml`: Manages open data import configurations.

## Profiles & Scalability
Service selection is handled via Docker profiles, allowing you to spin up only what you need.

```bash
COMPOSE_PROFILES=core docker compose up
```

This command starts only the **core** services (the database). You can extend the functionality by adding other profiles (e.g., `COMPOSE_PROFILES=core,api,pgadmin`).
