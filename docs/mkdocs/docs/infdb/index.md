# InfDB - Infrastructure and Energy Database

<p align="center">
  <img src="../assets/img/logo_infdb_text.png" alt="InfDB logo" width="00"/>
</p>

InfDB is a modular and flexible data platform built on dockerized services that can be easily activated and configured for specific use cases. This architecture ensures portability across all platforms. By providing standardized interfaces and APIs, InfDB fosters an extensible ecosystem that empowers users to integrate custom tools and workflows seamlessly.

![InfDB Overview](../assets/img/infdb-overview.png)

As shown in the diagram above, the architecture is composed of two main components:

: :fontawesome-solid-gears: **[Services](services/index.md)** – Dockerized open-source software providing base functionality.
: :material-tools: **[Tools](../tools/index.md)** – Software interacting with the InfDB.

## Services
InfDB services follow microservice architecture principles, enabling independent development and deployment while improving modularity, scalability, and adaptability.

For a comprehensive list of integrated tools and additional information, see **[Services](services/index.md)**.

## Tools
The InfDB ecosystem includes a variety of tools designed to handle different aspects of data workflows. These so called tools are software that interact with InfDB and process data through standardized, open interfaces. This modular approach allows you to tackle problems of any complexity by combining different tools into custom toolchains.

For a comprehensive list of integrated tools and additional information, see **[Tools](../tools/index.md)**.

## Python Package
Moreover, there is a python package `infdb` that can be used to interact with the InfDB database and services. It provides functionalities for database connections, logging, configuration management, and utility functions. You can find more information about the package in the **[API -> pyinfdb](../api/pyinfdb/index.md)**.