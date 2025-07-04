# Development Setup Guide
This guide provides comprehensive instructions for setting up a development environment for the InfDB project.
## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Development Setup](#docker-development-setup)
4. [IDE Configuration](#ide-configuration)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)
## Prerequisites
Before setting up the development environment, ensure you have the following installed:
- **Python 3.10 or higher**: Required for running the application.
- **Git**: For version control and cloning the repository.
- **Docker and Docker Compose**: For containerized development and running the database services.
- **IDE with Python support**: Visual Studio Code, PyCharm, or any other IDE with good Python support.
## Local Development Setup
Follow these steps to set up a local development environment without Docker:
### 1. Clone the Repository
```bash
git clone https://gitlab.lrz.de/tum-ens/need/database.git
cd database
```

### 2. Set Up Virtual Environment
Create and activate a virtual environment to isolate dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# For Windows
venv\Scripts\activate

# For Linux/MacOS
source venv/bin/activate
```

### 3. Install Dependencies
Install the required packages:

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the root directory with the following content:

```
# TimescaleDB Configuration
TIMESCALE_USER=postgres
TIMESCALE_PASSWORD=password
TIMESCALE_HOST=127.0.0.1
TIMESCALE_PORT=5432
TIMESCALE_DB=timescaledb

# CityDB Configuration
CITYDB_USER=postgres
CITYDB_PASSWORD=password
CITYDB_HOST=127.0.0.1
CITYDB_PORT=5433
CITYDB_DB=citydb

# General Configuration
DEBUG=true
```

Adjust the values according to your local database configuration.

### 5. Start the Database Services
For local development, you need to run TimescaleDB and 3DCityDB. Use Docker Compose:

```bash
# Start the database services
docker-compose -f docker-compose.dev.yaml up -d
```

### 6. Initialize the 3DCityDB
Load test data into 3DCityDB:

```bash
# Import test data
docker-compose -f docker-compose.import.yaml up -d
```

### 7. Run the Application
Start the FastAPI application:

```bash
# Using uvicorn directly
uvicorn src.main:app --reload

# Or using the FastAPI CLI if available
fastapi dev src/main.py
```

## Docker Development Setup
Follow these steps to set up a development environment using Docker:

### 1. Clone the Repository
```bash
git clone https://gitlab.lrz.de/tum-ens/need/database.git
cd database
```

### 2. Build the Docker Image
```bash
docker-compose build
```

### 3. Start the Services
```bash
docker-compose up -d
```

### 4. Import Test Data
```bash
docker-compose -f docker-compose.import.yaml up -d
```

### 5. Access the Application
The application will be available at http://localhost:8000.

## IDE Configuration
Configure your IDE for optimal development experience:

### Visual Studio Code
1. **Install Extensions**:
   - Python extension
   - Pylance for improved type checking
   - Docker extension
   - GitLens for better Git integration

2. **Configure Settings**:
   - Set Python interpreter to your virtual environment
   - Enable format on save with Black
   - Configure Flake8 for linting

### PyCharm
1. **Configure Python Interpreter**:
   - Set the project interpreter to your virtual environment

2. **Install Plugins**:
   - Black formatter
   - Flake8 linter

3. **Configure Code Style**:
   - Set line length to 88 characters
   - Enable PEP 8 checks

## Testing
Run tests to ensure your development environment is set up correctly:

### Running Tests
```bash
# Run all tests
pytest

# Run specific test files
pytest tests/unit/test_models.py

# Run tests with coverage report
pytest --cov=src tests/
```

### Writing Tests
Follow these guidelines when writing tests:
- Place unit tests in the `tests/unit` directory
- Place integration tests in the `tests/integration` directory
- Place end-to-end tests in the `tests/e2e` directory
- Use descriptive test names that explain what is being tested

## Troubleshooting
Common issues and their solutions:

### Database Connection Issues
- Ensure Docker containers are running: `docker ps`
- Check environment variables in `.env` file
- Verify port mappings in `docker-compose.yaml`

### Import Data Issues
- Check Docker logs: `docker-compose logs -f`
- Ensure volume paths are correct
- Verify database credentials

### Application Startup Issues
- Check for Python version compatibility
- Verify all dependencies are installed
- Look for error messages in the console output
