from fastapi import HTTPException, Query
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from src.schemas.resolution import ResolutionEnum
from src.services.citydb_service import CityDBService

router = InferringRouter(prefix="/city")


@cbv(router)
class CityDbRouter:
    cityDbService = CityDBService()

    @router.post("/rasters", tags=["Citydb"])
    async def generateRasterTable(self, resolution: ResolutionEnum = Query):
        result = self.cityDbService.getRasterCenters(resolution)
        if result:
            raise HTTPException(status_code=404, detail="Table was initialized before, skipping")

        self.cityDbService.generateRasterRelatedTables(resolution)
        return {
            "message": "Raster table filled successfully",
        }

    @router.get("/rasters", tags=["Citydb"])
    async def getRasterCenters(self, resolution: int = Query):
        result = self.cityDbService.getRasterCenters(resolution)
        if not result:
            raise HTTPException(status_code=404, detail="No data found")
        return result

    @router.get("/rasters/building/{building_id}", tags=["Citydb"])
    async def getRasterCenter(self, buildingId: int, resolution: int = Query):
        result = self.cityDbService.getRasterCenter(buildingId, resolution)
        if not result:
            raise HTTPException(status_code=404, detail="No data found")
        return result
