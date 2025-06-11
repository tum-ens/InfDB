# Coding Guidelines and Best Practices

This document outlines coding guidelines and best practices for the InfDB project, focusing on creating maintainable, efficient, and high-quality code for energy infrastructure digital twins. These guidelines are designed to help both new and existing developers contribute effectively to the project.

## Purpose

The purpose of these coding guidelines is to establish a consistent, maintainable, and high-quality codebase for the InfDB project. By following these guidelines, we aim to:

- **Ensure Code Consistency**: Establish uniform coding practices across the project to make the codebase more readable and maintainable.
- **Improve Collaboration**: Enable developers to work together more effectively by following shared conventions and practices.
- **Reduce Technical Debt**: Prevent the accumulation of technical debt by enforcing best practices from the start.
- **Enhance Code Quality**: Produce robust, efficient, and secure code that meets the specific needs of energy infrastructure digital twins.
- **Facilitate Onboarding**: Help new developers quickly understand the project structure and coding expectations.
- **Support Domain-Specific Requirements**: Address the unique challenges of energy system modeling, time-series data handling, and geospatial analysis.

These guidelines are not meant to be restrictive but rather to provide a framework that promotes code quality while allowing for innovation and creativity in solving complex energy domain problems.

## Table of Contents
1. [Technology Stack](#technology-stack)
2. [Project Structure](#project-structure)
3. [Code Style and Formatting](#code-style-and-formatting)
4. [Documentation Standards](#documentation-standards)
5. [Testing Practices](#testing-practices)
6. [Error Handling](#error-handling)
7. [Security Considerations](#security-considerations)
8. [Performance Optimization](#performance-optimization)
9. [Git Workflow](#git-workflow)
10. [Code Review Process](#code-review-process)
11. [Development Environment Setup](#development-environment-setup)
12. [Energy Domain-Specific Guidelines](#energy-domain-specific-guidelines)
13. [Dependency Management](#dependency-management)
14. [CI/CD Practices](#cicd-practices)
15. [Monitoring and Observability](#monitoring-and-observability)

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL with PostGIS and TimescaleDB extensions, 3DCityDB
- **ORM**: SQLModel
- **Authentication**: API key authentication (with OAuth2 planned for future)
- **API Documentation**: Swagger/OpenAPI

### Database
- **Primary Database**: PostgreSQL
- **Extensions**: 
  - PostGIS for geographical data
  - TimescaleDB for time-series data
  - 3DCityDB for urban modeling

### Deployment
- **Containerization**: Docker
- **CI/CD**: GitLab CI

## Project Structure

The project follows a modular architecture with separate directories for different components:

```
/
├── src/                    # Main application package
│   ├── api/                # API endpoints
│   │   ├── cityRouter.py   # City data endpoints
│   │   └── weatherRouter.py # Weather data endpoints
│   ├── core/               # Core application code
│   │   ├── dbConfig.py     # Database configuration
│   │   └── ...
│   ├── db/                 # Database
│   │   ├── bases.py        # Base models
│   │   ├── connection.py   # Database connection handling
│   │   ├── models/         # Database models
│   │   └── repositories/   # Database repositories
│   ├── exceptions/         # Custom exception classes
│   ├── externals/          # External API integrations
│   ├── schemas/            # Data schemas and validation
│   ├── services/           # Business logic services
│   └── main.py             # Application entry point
├── docs/                   # Documentation
├── tests/                  # Test suite
└── docker/                 # Docker configuration files
```

## Code Style and Formatting

### Python Style Guide
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) standards for all Python code.
- Use 4 spaces for indentation (no tabs).
- Limit line length to 88 characters (as configured in `.flake8`).
- Use meaningful variable and function names that clearly describe their purpose.

### Automated Formatting
- Use [Black](https://black.readthedocs.io/) for automatic code formatting:
  ```bash
  pip install black
  black src/
  ```
- Use [Flake8](https://flake8.pycqa.org/) for linting:
  ```bash
  pip install flake8
  flake8 src/
  ```
- Use [isort](https://pycqa.github.io/isort/) to sort imports:
  ```bash
  pip install isort
  isort src/
  ```

### Type Annotations
- Use type hints for all function parameters and return values:
  ```python
  def get_raster_center(building_id: int, resolution: int) -> dict:
      # Function implementation
  ```
- Use `Optional[Type]` for parameters that can be None.
- Use `Union[Type1, Type2]` for parameters that can be multiple types.
- Use `List[Type]`, `Dict[KeyType, ValueType]`, etc. for container types.

## Documentation Standards

### Docstrings
- Use Google-style docstrings for all modules, classes, and functions:
  ```python
  def get_raster_center(building_id: int, resolution: int) -> dict:
      """Retrieves the raster center for a specific building.

      Args:
          building_id: The ID of the building.
          resolution: The resolution in meters.

      Returns:
          A dictionary containing the raster center coordinates.

      Raises:
          HTTPException: If no data is found.
      """
  ```

### Module-Level Docstring
```python
"""Brief module description.

This module demonstrates the Google-style docstring format. It provides
several examples of documenting different types of objects and methods.

Attributes:
    module_level_variable1 (int): Module level variables can be documented here.
    module_level_variable2 (str): An example of an inline attribute docstring.
"""
```

### Class Docstring
```python
class ExampleClass:
    """A summary line for the class.

    Attributes:
        attr1 (str): Description of `attr1`.
        attr2 (int, optional): Description of `attr2`, which is optional.
    """
```

### Code Comments
- Write comments for complex logic or non-obvious implementations.
- Avoid redundant comments that merely repeat what the code does.
- Use TODO comments for planned improvements, with issue numbers when applicable:
  ```python
  # TODO: Optimize query performance (#123)
  ```

### Project Documentation
- Maintain comprehensive API documentation using [mkdocstrings](https://github.com/mkdocstrings/mkdocstrings).
- Update the `CHANGELOG.md` file for all significant changes.
- Include usage examples in documentation for complex features.

## Testing Practices

### Test Coverage
- Aim for high test coverage, especially for critical components.
- Write unit tests for all public functions and methods.
- Use integration tests for API endpoints and database interactions.

### Test Organization
- Organize tests to mirror the project structure.
- Name test files with a `test_` prefix.
- Group related tests in test classes.

### Test Tools
- Use [pytest](https://docs.pytest.org/) as the testing framework.
- Use [pytest-cov](https://pytest-cov.readthedocs.io/) for coverage reporting.
- Use [pytest-mock](https://pytest-mock.readthedocs.io/) for mocking dependencies.

### Test Best Practices
- Write independent tests that don't rely on the state of other tests.
- Use fixtures for common setup and teardown.
- Mock external dependencies to ensure tests are fast and reliable.
- Test edge cases and error conditions.

### Example Test
```python
import pytest
from src.services.citydb_service import CityDBService

def test_get_raster_center():
    # Arrange
    service = CityDBService()
    building_id = 123
    resolution = 100

    # Act
    result = service.getRasterCenter(building_id, resolution)

    # Assert
    assert result is not None
    assert "raster_id" in result
    assert "longitude" in result
    assert "latitude" in result
```

## Error Handling

### Error Messages
- Provide clear, actionable error messages.
- Include relevant context in error messages.
- Use structured error responses for API endpoints:
  ```python
  {
      "error": "Invalid weather parameter",
      "details": "Parameter 'temperature' is not available for the specified date range."
  }
  ```

### Logging
- Use the Python `logging` module for all logging.
- Configure appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
- Include relevant context in log messages.
- Avoid logging sensitive information.

## Security Considerations

### Input Validation
- Validate all user inputs using Pydantic models (within SQLModel).
- Implement strict type checking for API parameters.
- Use parameterized queries to prevent SQL injection.

### Authentication and Authorization
- Implement API key authentication as specified in requirement #21.
- Validate API keys for all protected endpoints.
- Implement role-based access control for different user types.

### Data Protection
- Encrypt sensitive data in transit and at rest.
- Implement proper error handling to avoid leaking sensitive information.
- Follow the principle of least privilege for database access.

## Performance Optimization

### Database Optimization
- Use appropriate indexes for frequently queried fields.
- Optimize SQL queries for performance.
- Use database connection pooling.
- Implement caching for frequently accessed data.

### API Optimization
- Use async/await for I/O-bound operations.
- Implement pagination for endpoints that return large datasets.
- Use appropriate HTTP status codes and headers.
- Implement rate limiting for public APIs.

### Resource Management
- Close database connections and file handles properly.
- Use context managers for resource cleanup.
- Monitor memory usage and optimize memory-intensive operations.

## Git Workflow

### Branch Strategy
- Follow the GitFlow branching model:
  - `main`: Production-ready code
  - `develop`: Integration branch for features
  - Feature branches: `feature/<issue-number>-<description>`
  - Hotfix branches: `hotfix/<issue-number>-<description>`
  - Release branches: `release/v<version>`

### Commit Messages
- Write clear, descriptive commit messages.
- Use the imperative mood ("Add feature" not "Added feature").
- Reference issue numbers in commit messages.
- Keep commits focused on a single change.

### Pull Requests
- Create descriptive pull request titles and descriptions.
- Link pull requests to issues.
- Request reviews from appropriate team members.
- Address all review comments before merging.

## Code Review Process

### Review Checklist
- Code follows style guidelines.
- Tests are included and pass.
- Documentation is updated.
- No security vulnerabilities are introduced.
- Performance implications are considered.
- Error handling is appropriate.

### Review Etiquette
- Be respectful and constructive in reviews.
- Focus on the code, not the person.
- Explain the reasoning behind suggestions.
- Acknowledge good practices and improvements.

## Development Environment Setup

### Local Environment
- Use virtual environments for isolation:
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  pip install -r requirements.txt
  ```

### Docker Environment
- Use Docker for consistent development environments:
  ```bash
  docker-compose -f docker-compose.local.yaml up -d
  ```

### IDE Configuration
- Configure your IDE to use Black and Flake8.
- Set up appropriate file templates with docstring placeholders.
- Configure EditorConfig for consistent formatting.

### Pre-commit Hooks
- Install pre-commit hooks to enforce code quality:
  ```bash
  pip install pre-commit
  pre-commit install
  ```

## Energy Domain-Specific Guidelines

### Energy Network Modeling
- Follow industry standards for modeling energy networks:
  - Use proper terminology for electrical components (transformers, substations, etc.)
  - Implement correct relationships between network components
  - Validate network topology for physical correctness

### Time Series Data Handling
- Implement appropriate time series models for energy data:
  - Use TimescaleDB for efficient storage and querying
  - Include metadata for time series (source, quality, etc.)
  - Handle different time resolutions appropriately

### Geospatial Data Management
- Follow best practices for geospatial data:
  - Use appropriate coordinate systems
  - Implement proper validation for geospatial data
  - Optimize geospatial queries for performance

### Energy Balance Calculations
- Implement energy balance calculations correctly:
  - Validate physical constraints
  - Handle units consistently
  - Document assumptions and limitations

### Domain-Driven Design
- Use domain-driven design principles for energy systems:
  ```python
  class Transformer:
      def __init__(self, id: str, capacity: float):
          self.id = id
          self.capacity = capacity
          self.status = TransformerStatus.OFFLINE

      def connect(self) -> Result[None, Error]:
          if self.status == TransformerStatus.ONLINE:
              return Result.failure(Error("Transformer already online"))

          # Domain logic for connecting a transformer
          self.status = TransformerStatus.ONLINE
          return Result.success(None)
  ```

### Event-Driven Architecture
- Implement event-driven architecture for grid state changes:
  ```python
  @dataclass
  class TransformerStateChangedEvent:
      transformer_id: str
      previous_state: TransformerStatus
      new_state: TransformerStatus
      timestamp: datetime
      reason: Optional[str] = None

  class TransformerStateChangeHandler:
      async def handle(self, event: TransformerStateChangedEvent) -> None:
          # Update grid state
          # Notify affected components
          # Log for audit purposes
  ```

## Dependency Management

### Package Management
- Use `pip` and `requirements.txt` for dependency management.
- Pin dependencies to specific versions for reproducibility.
- Separate development and production dependencies.

### Dependency Updates
- Regularly update dependencies to address security vulnerabilities.
- Test thoroughly after dependency updates.
- Document breaking changes in dependency updates.

## CI/CD Practices

### Continuous Integration
- Run tests automatically on all branches.
- Enforce code quality checks in CI pipeline.
- Generate test coverage reports.

### Continuous Deployment
- Automate deployment to staging and production environments.
- Implement blue-green deployments for zero-downtime updates.
- Include smoke tests after deployment.

### Pipeline Configuration
- Configure GitLab CI pipeline in `.gitlab-ci.yml`:
  ```yaml
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
  ```

## Monitoring and Observability

### Logging Infrastructure
- Implement structured logging for better analysis.
- Use log aggregation tools for centralized logging.
- Include context information in logs.

### Metrics Collection
- Collect performance metrics for critical components.
- Monitor database performance and query times.
- Track API response times and error rates.

### Alerting
- Set up alerts for critical issues.
- Define appropriate thresholds for alerts.
- Implement escalation procedures for alerts.
