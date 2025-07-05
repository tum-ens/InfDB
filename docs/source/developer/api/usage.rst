API Usage and Extension
=======================

Using the API
-------------

You can use any HTTP client to interact with the API. Here are examples using ``curl`` and Python’s ``requests`` library.

.. tip::

   Please follow the best practices outlined in the `FastAPI documentation <https://fastapi.tiangolo.com/>`_,
   especially the sections on **Documentation** and **Community Guidelines**.

**Using curl**

.. code-block:: bash

   curl -X GET "http://localhost:8000/city/rasters?resolution=100"

   curl -X POST "http://localhost:8000/weather/weather-data/100" \
     -H "Content-Type: application/json" \
     -d '{"dateRange": {"startDate": "2023-01-01", "endDate": "2023-01-31"}, "sensorNames": ["temperature", "humidity"]}'

**Using Python requests**

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

Adding New Endpoints
^^^^^^^^^^^^^^^^^^^^

To add new endpoints to the API, follow these steps:

1. **Create or update a router file** in the ``src/api`` directory:

   .. code-block:: python

      from fastapi import APIRouter, Query
      from src.schemas.your_schema import YourSchema
      from src.services.your_service import YourService

      router = APIRouter(prefix="/your-route", tags=["Your Tag"])

      @router.get("/")
      async def get_items(param: str = Query(None)):
          service = YourService()
          return service.get_items(param)

      @router.post("/")
      async def create_item(item: YourSchema):
          service = YourService()
          return service.create_item(item)

2. **Include your router** in ``src/main.py``:

   .. code-block:: python

      from fastapi import FastAPI
      from .api.your_router import router as your_router

      app = FastAPI()
      app.include_router(your_router)

3. **Create necessary schemas** in ``src/schemas``:

   .. code-block:: python

      from pydantic import BaseModel
      from typing import Optional

      class YourSchema(BaseModel):
          name: str
          description: Optional[str] = None
          value: float

4. **Service logic** in ``src/services``:

   .. code-block:: python

      class YourService:
          def __init__(self):
              self.repository = YourRepository()

          def get_items(self, param):
              return self.repository.get_items(param)

          def create_item(self, item: YourSchema):
              return self.repository.create_item(item)

5. **Repository logic** in ``src/db/repositories``:

   .. code-block:: python

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

6. **Database model** in ``src/db/models``:

   .. code-block:: python

      class YourModel(SQLModel, table=True):
          __tablename__ = "your_table"
          id: Optional[int] = Field(default=None, primary_key=True)
          name: str
          description: Optional[str] = None
          value: float
