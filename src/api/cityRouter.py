from fastapi import APIRouter, HTTPException, Path
from src.services.citydb_service import CityDBService

class CityRouter:
    def __init__(self):
        self.city_db_service = CityDBService()
        self.router = APIRouter(prefix="/city")
        self.register_routes()

    def register_routes(self):
        self.router.get("/{gmlId}")(self.get)

    async def get(self, gmlId: str = Path(..., regex=r"^[A-Z]+_[A-Z0-9]+_\d+$")):
        result = self.city_db_service.get(gmlId)
        if not result:
            raise HTTPException(status_code=404, detail=f"No city data found")
        return result

    def get_router(self):
        return self.router
