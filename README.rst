API Development Guide
=====================

This guide provides information for developers who want to use or extend the InfDB API.

API Overview
------------

InfDB provides a RESTful API built with FastAPI that exposes two main routes:

- ``/city`` — For accessing 3D city model data, including buildings and their spatial attributes  
- ``/weather`` — For accessing time-series weather data linked to spatial regions

The API is:

- **RESTful**: Follows REST principles  
- **JSON-based**: Uses JSON in request/response bodies  
- **Auto-documented**: OpenAPI docs via FastAPI  
- **Type-safe**: Enforced with Python type hints and Pydantic

Docs available at:

- Swagger UI: http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc  

Endpoints
---------

City Raster Endpoints
^^^^^^^^^^^^^^^^^^^^^

- ``POST /city/rasters?resolution={resolution}``  
  Generate rasters at the given resolution.

- ``GET /city/rasters?resolution={resolution}``  
  List all rasters of that resolution.

- ``GET /city/rasters/building/{building_id}?resolution={resolution}``  
  Return the raster cell(s) a building belongs to.

Weather Data Endpoints
^^^^^^^^^^^^^^^^^^^^^^

- ``POST /weather-data/{resolution}``  
  Insert weather data for a given resolution.  

  **Request Body:**

  - ``dateRange`` — object with ``startDate``, ``endDate``  
  - ``sensorNames`` — list of sensor types

- ``GET /weather-data/{resolution}``  
  Query weather data by resolution.  

  **Optional Query Parameters:**

  - ``buildingId``  
  - ``startTime``  
  - ``endTime``  

Using the API
-------------

**With curl**

.. code-block:: bash

   curl -X GET "http://localhost:8000/city/rasters?resolution=100"

   curl -X POST "http://localhost:8000/weather/weather-data/100" \
     -H "Content-Type: application/json" \
     -d '{"dateRange": {"startDate": "2023-01-01", "endDate": "2023-01-31"}, "sensorNames": ["temperature", "humidity"]}'

**With Python requests**

.. code-block:: python

   import requests

   response = requests.get("http://localhost:8000/city/rasters", params={"resolution": 100})
   rasters = response.json()

   weather_data = {
       "dateRange": {"startDate": "2023-01-01", "endDate": "2023-01-31"},
       "sensorNames": ["temperature", "humidity"]
   }
   response = requests.post("http://localhost:8000/weather/weather-data/100", json=weather_data)
   result = response.json()

Extending the API
-----------------

1. **Add router in ``src/api``**:

.. code-block:: python

   @router.post("/")
   async def create_item(item: YourSchema):
       return YourService().create_item(item)

2. **Register router in ``src/main.py``**:

.. code-block:: python

   app.include_router(your_router)

3. **Create Pydantic schema in ``src/schemas``**

.. code-block:: python

   class YourSchema(BaseModel):
       name: str
       value: float

4. **Service layer in ``src/services``**:

.. code-block:: python

   def create_item(self, item): return self.repo.create_item(item)

5. **Repository layer in ``src/db/repositories``**:

- **src/**: Main application package
  - **api/**: API endpoints (cityRouter.py, weatherRouter.py)
  - **core/**: Core application code (dbConfig.py, etc.)
  - **db/**: Database models and repositories
    - **models/**: SQLModel classes for database entities
    - **repositories/**: Data access layer for database operations
  - **exceptions/**: Custom exception classes
  - **externals/**: External API integrations (e.g., weather API)
  - **schemas/**: Data schemas and validation
  - **services/**: Business logic services
  - **main.py**: Application entry point
- **docs/**: Documentation
  - **architecture/**: System architecture documentation
  - **contributing/**: Contribution guidelines and code of conduct
  - **development/**: Developer guides and workflows
  - **guidelines/**: Project guidelines and standards
  - **operations/**: Operational guides and CI/CD documentation
  - **source/**: Source files for documentation
  - **img/**: Images used in documentation
- **dockers/**: Docker configuration files
- **tests/**: Test suite
  - **unit/**: Unit tests for individual components
  - **integration/**: Tests for component interactions
  - **e2e/**: End-to-end tests for the application
  - **conftest.py**: Pytest configuration and fixtures

   def create_item(self, item): session.add(...); session.commit()

6. **Model in ``src/db/models``**:

.. code-block:: python

   class YourModel(SQLModel, table=True): id: Optional[int] = Field(...)

API Design Best Practices
-------------------------

- Use correct HTTP methods  
- Prefer query params for filters  
- Add type hints and docstrings  
- Paginate and filter where needed  
- Keep endpoints meaningful and consistent

Error Handling
--------------

- **200 OK** – Success  
- **201 Created** – Resource created  
- **400 Bad Request** – Invalid input  
- **404 Not Found** – Resource missing  
- **422 Unprocessable Entity** – Validation error  
- **500 Internal Server Error** – Unexpected failure

**Custom Exceptions Example:**

.. code-block:: python

   raise HTTPException(status_code=404, detail="Item not found")

Authentication
--------------

Not yet implemented. Future support may include:

- API keys or OAuth2  
- Scoped tokens and roles  

Rate Limiting
-------------

Planned but not implemented.

Best Practices
--------------

Performance
^^^^^^^^^^^

- Use ``async`` for endpoints  
- Index time and raster ID columns  
- Paginate long results  
- Use Redis or in-memory cache if needed

Documentation
^^^^^^^^^^^^^

- Use clear names and descriptions  
- Provide OpenAPI examples  
- Keep ``/docs`` and ``/redoc`` clean

Testing
^^^^^^^

- Use ``TestClient`` from FastAPI  
- Mock DB access where needed  
- Cover edge cases and invalid input

Security
^^^^^^^^

CI/CD Workflow
==============

The CI/CD workflow is set up using GitLab CI/CD.
The workflow runs tests, checks code style, and builds the documentation on every push to the repository.
You can view workflow results directly in the repository's CI/CD section.
For detailed information about the CI/CD workflow, see the `CI/CD Guide <docs/operations/CI_CD_Guide.md>`_.

Development Resources
=====================
The following resources are available to help developers understand and contribute to the project:

Coding Guidelines
-----------------
The `Coding Guidelines <docs/guidelines/coding_guidelines.md>`_ document outlines the coding standards and best practices for the project.
Start here when trying to understand the project as a developer.

Architecture Documentation
--------------------------
The `Architecture Documentation <docs/architecture/index.rst>`_ provides an overview of the system architecture, including the database schema, components, and integration points.

Developer Guides
----------------
- `Development Setup Guide <docs/development/setup.md>`_: Comprehensive instructions for setting up a development environment
- `Contribution Workflow <docs/development/workflow.md>`_: Step-by-step process for contributing to the project
- `API Development Guide <docs/development/api_guide.md>`_: Information for developers who want to use or extend the API
- `Database Schema Documentation <docs/development/database_schema.md>`_: Detailed information about the database schema

Contribution Guidelines
-----------------------
- `Contributing Guide <docs/contributing/CONTRIBUTING.md>`_: Guidelines for contributing to the project
- `Code of Conduct <docs/contributing/CODE_OF_CONDUCT.md>`_: Community standards and expectations
- `Release Procedure <docs/contributing/RELEASE_PROCEDURE.md>`_: Process for creating new releases

Operations Documentation
------------------------
- `CI/CD Guide <docs/operations/CI_CD_Guide.md>`_: Detailed information about the CI/CD workflow

Contribution and Code Quality
=============================
Everyone is invited to develop this repository with good intentions.
Please follow the workflow described in the `CONTRIBUTING.md <docs/contributing/CONTRIBUTING.md>`_.

Coding Standards
----------------
This repository follows consistent coding styles. Refer to `CONTRIBUTING.md <docs/contributing/CONTRIBUTING.md>`_ and the `Coding Guidelines <docs/guidelines/coding_guidelines.md>`_ for detailed standards.

Pre-commit Hooks
----------------
Pre-commit hooks are configured to check code quality before commits, helping enforce standards.

Changelog
---------
The changelog is maintained in the `CHANGELOG.md <CHANGELOG.md>`_ file.
It lists all changes made to the repository.
Follow instructions there to document any updates.

License and Citation
====================
| The code of this repository is licensed under the **MIT License** (MIT).
| See `LICENSE <LICENSE>`_ for rights and obligations.
| See the *Cite this repository* function or `CITATION.cff <CITATION.cff>`_ for citation of this repository.
| Copyright: `TU Munich - ENS <https://www.epe.ed.tum.de/en/ens/homepage/>`_ | `MIT <LICENSE>`_


.. |badge_license| image:: https://img.shields.io/badge/license-MIT-blue
    :target: LICENSE
    :alt: License

.. |badge_documentation| image:: https://img.shields.io/badge/docs-available-brightgreen
    :target: https://gitlab.lrz.de/tum-ens/need/database
    :alt: Documentation

.. |badge_contributing| image:: https://img.shields.io/badge/contributions-welcome-brightgreen
    :target: docs/contributing/CONTRIBUTING.md
    :alt: contributions

.. |badge_contributors| image:: https://img.shields.io/badge/contributors-0-orange
    :alt: contributors

.. |badge_repo_counts| image:: https://img.shields.io/badge/repo-count-brightgreen
    :alt: repository counter

.. |badge_issue_open| image:: https://img.shields.io/badge/issues-open-blue
    :target: https://gitlab.lrz.de/tum-ens/need/database/-/issues
    :alt: open issues

.. |badge_issue_closes| image:: https://img.shields.io/badge/issues-closed-green
    :target: https://gitlab.lrz.de/tum-ens/need/database/-/issues
    :alt: closed issues

.. |badge_pr_open| image:: https://img.shields.io/badge/merge_requests-open-blue
    :target: https://gitlab.lrz.de/tum-ens/need/database/-/merge_requests
    :alt: open merge requests

.. |badge_pr_closes| image:: https://img.shields.io/badge/merge_requests-closed-green
    :target: https://gitlab.lrz.de/tum-ens/need/database/-/merge_requests
    :alt: closed merge requests
