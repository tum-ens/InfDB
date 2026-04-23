# Requirements

Before installing InfDB, ensure your capabilities meet the following requirements.

## System Requirements

-   **Operating System**: Linux (recommended), macOS, or Windows (via WSL2).
-   **Hardware**:
    -   Minimum 8GB RAM (16GB recommended for heavy geospatial workloads).
    -   20GB+ free disk space (depending on data volume).

## Software Prerequisites

The InfDB runs primarily on containerized infrastructure. You need:

1.  **[Git](https://git-scm.com/)**: To clone the repository.
2.  **[Docker](https://docs.docker.com/get-docker/)**: Engine version 20.10+ recommended.
3.  **[Docker Compose](https://docs.docker.com/compose/install/)**: Version 2.0+ (usually included with modern Docker Desktop/Engine).

!!! note "Windows Users"
    If you are on Windows, we strongly recommend using [WSL2 (Windows Subsystem for Linux)](https://learn.microsoft.com/en-us/windows/wsl/install) to run Docker, as it offers significantly better performance for file system operations compared to the legacy Hyper-V backend.