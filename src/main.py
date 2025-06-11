from fastapi import FastAPI
from .api.cityRouter import router as city_router
from .api.weatherRouter import router as weather_router
from .db.connection import init_db


init_db()
app = FastAPI()
app.include_router(city_router)
app.include_router(weather_router)
