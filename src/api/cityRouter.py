from fastapi import HTTPException, Query
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from src.services.citydb_service import CityDBService


router = InferringRouter(prefix="/city")
city_db_service = CityDBService()


@cbv(router)
class CityDbRouter:
    @router.get("/grids")
    async def get_grid_centers(self):
        result = city_db_service.getGridCenters()
        if not result:
            raise HTTPException(status_code=404, detail="No data found")
        return {
            "message": "Data retrieved successfully",
            "data": [{
                "building_id": data.building_id,
                "grid_id": data.grid_id,
                "longitude": data.longitude,
                "latitude": data.latitude,
            } for data in result]
        }

    @router.get("/grids/building/{buildingId}")
    async def get_grid_center(buildingId: int, resolution: int = Query):
        result = city_db_service.getGridCenter(buildingId, resolution)
        if not result:
            raise HTTPException(status_code=404, detail="No data found")
        return {
            "message": "Data retrieved successfully",
            "data": {
                "building_id": result.building_id,
                "grid_id": result.grid_id,
                "longitude": result.longitude,
                "latitude": result.latitude,
            }
        }
