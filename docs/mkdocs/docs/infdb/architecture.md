---
icon: material/domain
---
# InfDB Architecture :material-domain:

The architecture of InfDB is designed to be modular, scalable, and flexible, allowing for easy integration of various data sources and tools. This architecture is implemented using Docker Compose to orchestrate multiple services, including the core database, data importers, and various processing tools.

![InfDB Architecture](infdb-architecture.png)

## Core Components

-   **Docker Compose**: The extensive `compose.yml` file controls all containerized services.
-   **Helper Script**: Bash script (`infdb.sh`,) simplify common management tasks such as starting, stopping, removing and loading data.
-   **Configuration**:
    -   `.env`: Controls global settings like credentials, ports, and paths.
    -   `config-infdb-import.yml`: Manages open data import configurations.

## Profiles & Scalability
Service selection is handled via Docker profiles, allowing you to spin up only what you need. This modular approach supports scalability and customization, enabling users to add new services or tools as needed without affecting the core architecture.
