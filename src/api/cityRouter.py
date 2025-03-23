from fastapi import HTTPException, Query
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from src.services.citydb_service import CityDBService


router = InferringRouter(prefix="/city")
city_db_service = CityDBService()


@cbv(router)
class CityDbRouter:
    @router.post("/grids")
    async def generate_grid_table(self, resolution: int = Query):
        result = city_db_service.getGridCenters(resolution)
        if result:
            raise HTTPException(status_code=404, detail="Table was initialized before skipping")
        
        # these 2 should happen in transaction or atleast under 1 commit.
        city_db_service.generateGrids(resolution)
        city_db_service.generateBuilding2GridMappings(resolution)
        return {
            "message": "Grid table filled successfully",
        }

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

    @router.get("/grids/building/{building_id}")
    async def get_grid_center(self, building_id: int, resolution: int = Query):
        print(building_id)
        result = city_db_service.getGridCenter(building_id, resolution)
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
