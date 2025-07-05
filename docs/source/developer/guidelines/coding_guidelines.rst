Purpose
-------

The purpose of these coding guidelines is to establish a consistent, maintainable, and high-quality codebase for the InfDB project. By following these guidelines, we aim to:

- **Ensure Code Consistency**
- **Improve Collaboration**
- **Reduce Technical Debt**
- **Enhance Code Quality**
- **Facilitate Onboarding**
- **Support Domain-Specific Requirements**

These guidelines provide a framework that promotes code quality while allowing flexibility.

Technology Stack
----------------

**Backend**

- FastAPI
- PostgreSQL (with PostGIS, TimescaleDB, 3DCityDB)
- SQLModel
- API key authentication (OAuth2 planned)
- Swagger/OpenAPI

**Deployment**

- Docker
- GitLab CI

Project Structure
-----------------

.. code-block:: text

    /
    ├── src/
    │   ├── api/
    │   ├── core/
    │   ├── db/
    │   ├── exceptions/
    │   ├── externals/
    │   ├── schemas/
    │   ├── services/
    │   └── main.py
    ├── docs/
    ├── tests/
    └── docker/

Code Style and Formatting
--------------------------

- Follow `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_
- Use 4 spaces, line length of 88
- Use meaningful names
- Use type hints and docstrings

.. code-block:: bash

    pip install black flake8 isort
    black src/
    flake8 src/
    isort src/

Documentation Standards
------------------------

Use Google-style docstrings:

.. code-block:: python

    def get_raster_center(building_id: int, resolution: int) -> dict:
        """Retrieves raster center.

        Args:
            building_id: Building ID.
            resolution: Resolution.

        Returns:
            Raster center coordinates.
        """

Testing Practices
------------------

- Use pytest, pytest-cov, pytest-mock
- Organize tests by feature
- Mock external services

.. code-block:: python

    def test_get_raster_center():
        # Arrange
        ...
        # Act
        ...
        # Assert
        ...

Error Handling
--------------

- Provide clear, structured error messages
- Use logging

.. code-block:: json

    {
        "error": "Invalid parameter",
        "details": "Temperature not available"
    }

Security Considerations
------------------------

- Validate inputs with Pydantic
- Use parameterized queries
- Validate API keys

Performance Optimization
-------------------------

- Add indexes for frequently queried fields
- Use async/await for I/O operations
- Implement caching if needed

Git Workflow
------------

- Use GitFlow:
  - `main`: production
  - `develop`: integration
  - `feature/*`, `hotfix/*`, `release/*`

- Write descriptive commits
- Reference issues in messages

Code Review Process
--------------------

Checklist:

- Code follows style guide
- Tests pass and are relevant
- Docs are updated
- No security issues
- Performance impact reviewed

Be constructive and respectful in reviews.

Development Environment Setup
------------------------------

.. code-block:: bash

    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt

    docker-compose -f docker-compose.local.yaml up -d

Energy Domain-Specific Guidelines
----------------------------------

.. code-block:: python

    class Transformer:
        def __init__(self, id: str, capacity: float):
            self.id = id
            self.capacity = capacity

    @dataclass
    class TransformerStateChangedEvent:
        transformer_id: str
        previous_state: TransformerStatus
        new_state: TransformerStatus
        timestamp: datetime
        reason: Optional[str] = None

Dependency Management
----------------------

- Use pip and pin versions
- Separate development and production requirements

CI/CD Practices
---------------

- GitLab CI example:

.. code-block:: yaml

    stages:
      - install
      - lint
      - test
      - build
      - deploy

    install_dependencies:
      stage: install
      script:
        - python -m venv venv
        - source venv/bin/activate
        - pip install -r requirements.txt

Monitoring and Observability
-----------------------------

- Use structured logging
- Collect performance metrics
- Set up alerts and escalation policies
