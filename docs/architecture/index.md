# InfDB Architecture Documentation
## Table of Contents
1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [Design Decisions](#design-decisions)
## System Overview
InfDB is designed as a comprehensive database system for creating digital twins of energy infrastructure with integrated geospatial and time-series capabilities. The system architecture follows a layered approach with clear separation of concerns.
The core of the system consists of a PostgreSQL database with specialized extensions (TimescaleDB, PostGIS, 3DCityDB) to handle different types of data. The application layer is built with FastAPI, providing a RESTful interface to interact with the database.
## Component Architecture
InfDB is composed of the following main components:
1. **Database Layer**: PostgreSQL with extensions for specialized data types:
   - TimescaleDB: Handles time-series data efficiently
   - PostGIS: Provides geospatial capabilities
   - 3DCityDB: Supports urban modeling and 3D city data
2. **API Layer**: FastAPI-based RESTful interface:
   - City Router: Handles geospatial data and building information
   - Weather Router: Manages time-series weather data
3. **Service Layer**: Business logic implementation:
   - CityDB Service: Handles operations related to city data
   - Weather Service: Manages weather data operations
4. **Repository Layer**: Data access layer:
   - CityDB Repository: Handles database operations for city data
   - Weather Repository: Manages database operations for weather data
5. **Model Layer**: Data models and schemas:
   - Database Models: SQLModel classes for database entities
   - Schemas: Pydantic models for data validation and serialization
6. **External Integrations**: Connections to external services:
   - Weather API: Integration with external weather data providers
## Data Flow
The data flow in InfDB follows these general patterns:
1. **Geospatial Data Flow**:
   - External GIS data → 3DCityDB → CityDB Repository → CityDB Service → API
2. **Time-Series Data Flow**:
   - External Weather API → Weather Service → Weather Repository → TimescaleDB → API
3. **Energy Infrastructure Data Flow**:
   - Energy Network Models → PostgreSQL → Repository Layer → Service Layer → API
## Design Decisions
The following key design decisions have shaped the architecture of InfDB:
1. **PostgreSQL with Extensions**: We chose PostgreSQL with specialized extensions rather than multiple database systems to simplify deployment and maintenance while still providing specialized capabilities for different data types.
2. **FastAPI Framework**: FastAPI was selected for its performance, automatic OpenAPI documentation, and native support for asynchronous operations, which is beneficial for handling time-series data queries.
3. **SQLModel ORM**: We chose SQLModel as it combines the best features of SQLAlchemy and Pydantic, providing both powerful ORM capabilities and robust data validation.
4. **Layered Architecture**: The system follows a clear separation of concerns with distinct layers (API, Service, Repository, Model), making it easier to maintain, test, and extend.
5. **Docker Containerization**: The application is containerized using Docker to ensure consistent deployment across different environments and simplify the setup of the complex database infrastructure.
