Core Operational Services
=========================

In addition to the main data components (3DCityDB and TimescaleDB), InfDB includes two key services that handle data import and solar potential analysis.

Data Loader
-----------

The Data Loader prepares the system. It sets up the necessary databases and tools automatically. 

When the system starts:

- All required services (such as the city model database and weather database) are launched together.
- Configurations for each service are read from internal settings files.
- Datasets are downloaded, organized, and stored in the right folders without needing manual steps.

**Supported Datasets:**

- Building models (LOD2)
- Street networks
- Administrative boundaries
- Postal code regions

These datasets are organized into folders automatically. Once the loader finishes, the system is ready to be used — either for browsing building data, accessing weather history, or running analyses.

Solar Potential Analysis
------------------------

InfDB also includes a solar potential calculation service, which helps estimate how much sunlight each building receives.

When the system starts:

1. Loads 3D building data into a temporary 3DCityDB v4.
2. Runs simulations to measure how much sunlight each roof surface receives.
3. Saves the results in the persistent 3DCityDB v5 so they can be viewed later or used in applications.
