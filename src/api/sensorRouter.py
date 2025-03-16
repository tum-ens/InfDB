from fastapi import HTTPException, Request
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from src.schemas.sensor_data import SensorData
from src.services.sensor_service import SensorService


router = InferringRouter(prefix="/sensor")
sensor_service = SensorService()


@cbv(router)
class SensorRouter:
    @router.post("/")
    async def insert_sensor_data(self, data: SensorData):
        result = sensor_service.insertSensorData(data)
        return {
            "message": "Data inserted successfully",
            "inserted_id": result
        }

    @router.get("/{gmlId}")
    async def get_by_gml_id(self, gmlId: str):
        result = sensor_service.getByGmlId(gmlId)
        if not result:
            raise HTTPException(status_code=404, detail=f"No sensor data found for gml_id: {gmlId}")
        return {
            "message": "Data retrieved successfully",
            "data": [{
                "id": data.id,
                "timestamp": data.timestamp,
                "gml_id": data.gml_id,
                "sensor_name": data.sensor_name,
                "value": data.value
            } for data in result]
        }

    @router.get("/")
    async def get(self, request: Request):
        query_params = dict(request.query_params)
        result = sensor_service.get(query_params)
        if not result:
            raise HTTPException(status_code=404, detail="No sensor data found")
        return {
            "message": "Data retrieved successfully",
            "data": [{
                "id": data.id,
                "timestamp": data.timestamp,
                "gml_id": data.gml_id,
                "sensor_name": data.sensor_name,
                "value": data.value
            } for data in result]
        }
