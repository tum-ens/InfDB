# API Development Guide

This guide provides information for developers who want to use or extend the InfDB API.

## Table of Contents
1. [API Overview](#api-overview)
2. [Using the API](#using-the-api)
3. [Extending the API](#extending-the-api)
4. [Error Handling](#error-handling)
5. [Authentication](#authentication)
6. [Best Practices](#best-practices)

## API Overview

InfDB provides a RESTful API built with FastAPI that exposes two main routes:

- **/city** — For accessing 3D city model data, including buildings and their spatial attributes
- **/weather** — For accessing time-series weather data linked to spatial regions

The API is designed to be:
- **RESTful**: Following REST principles for resource management
- **JSON-based**: Using JSON for request and response bodies
- **Well-documented**: With automatic OpenAPI documentation
- **Type-safe**: Leveraging Python type hints and Pydantic models

## Using the API

### API Documentation

FastAPI automatically generates interactive documentation for the API:

- **Swagger UI**: Available at http://localhost:8000/docs when running the application locally
- **ReDoc**: Available at http://localhost:8000/redoc for an alternative documentation view

These interfaces allow you to:
- Browse available endpoints
- See request and response schemas
- Test endpoints directly from the browser

### Making API Requests

You can use any HTTP client to interact with the API. Here are examples using `curl` and Python's `requests` library:

#### Using curl

```bash
# Get rasters at a specific resolution
curl -X GET "http://localhost:8000/city/rasters?resolution=100"

# Post weather data
curl -X POST "http://localhost:8000/weather/weather-data/100" \
  -H "Content-Type: application/json" \
  -d '{"dateRange": {"startDate": "2023-01-01", "endDate": "2023-01-31"}, "sensorNames": ["temperature", "humidity"]}'
```

#### Using Python requests

```python
import requests
import json

# Get rasters at a specific resolution
response = requests.get("http://localhost:8000/city/rasters", params={"resolution": 100})
rasters = response.json()

# Post weather data
weather_data = {
    "dateRange": {
        "startDate": "2023-01-01",
        "endDate": "2023-01-31"
    },
    "sensorNames": ["temperature", "humidity"]
}
response = requests.post(
    "http://localhost:8000/weather/weather-data/100",
    json=weather_data
)
result = response.json()
```

## Extending the API

### Adding New Endpoints

To add new endpoints to the API, follow these steps:

1. **Create or update a router file** in the `src/api` directory:

```python
from fastapi import APIRouter, Query
from src.schemas.your_schema import YourSchema
from src.services.your_service import YourService

router = APIRouter(prefix="/your-route", tags=["Your Tag"])

@router.get("/")
async def get_items(param: str = Query(None)):
    """Get items based on the provided parameter."""
    service = YourService()
    return service.get_items(param)

@router.post("/")
async def create_item(item: YourSchema):
    """Create a new item."""
    service = YourService()
    return service.create_item(item)
```

2. **Include your router** in the main application (`src/main.py`):

```python
from fastapi import FastAPI
from .api.your_router import router as your_router

app = FastAPI()
app.include_router(your_router)
```

3. **Create necessary schemas** in the `src/schemas` directory:

```python
from pydantic import BaseModel
from typing import Optional

class YourSchema(BaseModel):
    name: str
    description: Optional[str] = None
    value: float
```

4. **Implement service logic** in the `src/services` directory:

```python
from src.schemas.your_schema import YourSchema
from src.db.repositories.your_repository import YourRepository

class YourService:
    def __init__(self):
        self.repository = YourRepository()
    
    def get_items(self, param):
        return self.repository.get_items(param)
    
    def create_item(self, item: YourSchema):
        return self.repository.create_item(item)
```

5. **Create repository classes** in the `src/db/repositories` directory:

```python
from src.db.models.your_model import YourModel
from sqlmodel import Session, select
from src.core.dbConfig import your_engine

class YourRepository:
    def get_items(self, param):
        with Session(your_engine) as session:
            statement = select(YourModel)
            if param:
                statement = statement.where(YourModel.some_field == param)
            return session.exec(statement).all()
    
    def create_item(self, item):
        with Session(your_engine) as session:
            db_item = YourModel(**item.dict())
            session.add(db_item)
            session.commit()
            session.refresh(db_item)
            return db_item
```

6. **Define database models** in the `src/db/models` directory:

```python
from sqlmodel import Field, SQLModel
from typing import Optional

class YourModel(SQLModel, table=True):
    __tablename__ = "your_table"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    value: float
```

### API Design Best Practices

When extending the API, follow these best practices:

- **Use appropriate HTTP methods**:
  - GET for retrieving resources
  - POST for creating resources
  - PUT for updating resources
  - DELETE for removing resources

- **Use meaningful route names** that reflect the resources being manipulated

- **Version your API** if making breaking changes

- **Use query parameters** for filtering, sorting, and pagination

- **Use path parameters** for identifying specific resources

- **Use request bodies** for complex data structures

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of requests:

- **2xx**: Success
  - 200 OK: The request was successful
  - 201 Created: A new resource was created

- **4xx**: Client errors
  - 400 Bad Request: The request was malformed
  - 404 Not Found: The requested resource was not found
  - 422 Unprocessable Entity: Validation error

- **5xx**: Server errors
  - 500 Internal Server Error: An unexpected error occurred

### Implementing Error Handling

When implementing new endpoints, use FastAPI's built-in exception handling:

```python
from fastapi import HTTPException

@router.get("/{item_id}")
async def get_item(item_id: int):
    item = service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

For custom exceptions, define them in the `src/exceptions` directory:

```python
class YourCustomException(Exception):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details
```

Then handle them in your router:

```python
from src.exceptions.your_exception import YourCustomException

@router.post("/")
async def create_item(item: YourSchema):
    try:
        return service.create_item(item)
    except YourCustomException as e:
        raise HTTPException(status_code=400, detail={"error": str(e), "details": e.details})
```

## Authentication

Authentication is not yet implemented in the API, but it will be added in the future using API keys or OAuth2. When implementing authentication, follow these guidelines:

- Use FastAPI's security utilities
- Implement proper token validation
- Apply authentication to protected endpoints
- Use dependency injection for authentication

## Best Practices

### Performance Considerations

- Use async/await for I/O-bound operations
- Implement pagination for endpoints that return large datasets
- Use database indexes for frequently queried fields
- Consider caching for frequently accessed data

### Documentation

- Add docstrings to all API endpoints
- Include example requests and responses
- Document all parameters and return values
- Keep the documentation up-to-date with code changes

### Testing

- Write tests for all API endpoints
- Test both success and error cases
- Use FastAPI's TestClient for API testing
- Mock external dependencies in tests

### Security

- Validate all input data
- Use parameterized queries to prevent SQL injection
- Implement rate limiting for public endpoints
- Follow the principle of least privilege