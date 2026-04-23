# Development Process

## Documentation Requirements

- Maintain **up-to-date API documentation** using OpenAPI/Swagger
- Write **clear README files** for each major component
- Document **database schema** and relationships
- Create **entity-relationship diagrams** for the database
- Document **deployment procedures**
- Include **code examples** for common operations
- Update documentation with each significant change

### Docstrings

Use Google-style docstrings for all modules, classes, and functions:

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
- Maintain comprehensive API documentation using [Sphinx](https://github.com/sphinx-doc/sphinx).
- Update the `CHANGELOG.md` file for all changes, i.e. one entry per merge request.
- Include usage examples in documentation for complex features.

## Deployment Process

### Development Environment

- Use **Docker Compose** for local development
- Run the application with **hot reloading** enabled
- Use **development-specific configuration**
- Use **test data** for development

### Production Environment

- Deploy using **CI/CD pipeline**
- Run **comprehensive test suite** before deployment
- Use **production-specific configuration**
- Set up **monitoring and alerting**
- Configure **automatic backups**
- Implement **rollback procedures**

## Contribution and Code Review Process

### Pull Request Templates

Standardize PR descriptions by using the provided template.

### Code Review Standards 
  - At least one approval required before merging
  - Code author cannot approve their own PR
  - Automated tests must pass
  - Code style checks must pass

### Merge Criteria
  - All discussions must be resolved
  - CI pipeline must pass
  - Documentation and CHANGELOG.md must be updated

### Review Checklist
- Code follows style guidelines.
- Tests are included and pass.
- Documentation is updated.
- No security vulnerabilities are introduced.
- Performance implications are considered.
- Error handling is appropriate.

### Contribution Workflow Example

1. **Issue Creation**:
    ```
    Title: Add support for importing weather data from CSV files

    Description:
    Currently, the system only supports importing weather data via the API.
    We need to add support for importing data from CSV files to facilitate
    bulk data loading from existing datasets.

    Acceptance Criteria:
    - Support CSV files with standard format (columns: timestamp, raster_id, sensor_name, value)
    - Validate data before import
    - Handle errors gracefully with clear error messages
    - Add documentation for the new import feature
    ```

2. **Branch Creation**:
    ```bash
    git checkout develop
    git pull
    git checkout -b feature/123-csv-weather-import
    ```

3. **Implementation and Testing**:
    - Implement the feature following the coding guidelines
    - Write unit and integration tests
    - Update documentation

4. **Merge Request**:
   ```
   Title: Add CSV import support for weather data (#123)

   Description:
   This MR adds support for importing weather data from CSV files.

   Changes:
   - Add new endpoint `/weather/import/csv`
   - Implement CSV validation and parsing
   - Add error handling for malformed CSV files
   - Update documentation with usage examples

   Resolves #123
   ```

5. **Code Review Process**:
    - Reviewer provides feedback
    - Developer addresses feedback
    - Reviewer approves changes

6. **Merge and Deployment**:
    - Merge to develop branch
    - Deploy to staging environment
    - Verify functionality
    - Close the issue

## Version Control and Branching Strategy

### Branch Strategy

Follow the GitFlow branching model:

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

Example
  ```
  [Component] Short description (50 chars max)

  Detailed explanation if necessary. Wrap at 72 characters.
  Include motivation for change and contrast with previous behavior.

  Refs #123
  ```

### Pull Requests
- Use the pull request template.
- Create descriptive pull request titles and descriptions.
- Link pull requests to issues.
- Request reviews from appropriate team members.
- Address all review comments before merging.

### Version Tagging:
  - Follow [Semantic Versioning](https://semver.org/)
  - Tag all releases in Git
  - Include release notes with each tag

## Dependency Management

- **Dependency Documentation**:
    - Document all dependencies in `pyproject.toml` with pinned versions
    - Include comments explaining why each dependency is needed

- **Dependency Updates**:
    - Schedule regular dependency updates (monthly)
    - Test thoroughly after updates
    - Document any breaking changes

- **Dependency Approval Process**:
    - New dependencies must be approved by the team
    - Consider security, maintenance status, and license compatibility

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
