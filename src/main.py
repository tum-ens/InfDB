from fastapi import FastAPI
from src.api.routes import ApiRouter
from src.db.connection import init_db

init_db()
app = FastAPI()
api_routes = ApiRouter()
app.include_router(api_routes.get_router())