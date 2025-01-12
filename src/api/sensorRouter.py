from fastapi import APIRouter, HTTPException
from src.schemas.sensor_data import SensorData
from src.services.sensor_service import SensorService

class SensorRouter:
    def __init__(self):
        self.sensorService = SensorService()
        self.router = APIRouter(prefix="/sensor")
        self.register_routes()

    def register_routes(self):
        self.router.post("/")(self.insertSensorData)
        self.router.get("/{gmlId}")(self.getByGmlId)
        self.router.get("/")(self.get)
    
    async def insertSensorData(self, data: SensorData):
        result = self.sensorService.insertSensorData(data)
        return {
            "message": "Data inserted successfully",
            "inserted_id": result
        }
        
    async def getByGmlId(self, gmlId: str):
        print(gmlId)
        result = self.sensorService.getByGmlId(gmlId)
        if not result:
            raise HTTPException(status_code=404, detail=f"No sensor data found for gml_id: {gmlId}")
        return {
                "message": "Data retrieved successfully",
                "data": [
                    {
                        "id": data.id,
                        "timestamp": data.timestamp,
                        "gml_id": data.gml_id,
                        "sensor_name": data.sensor_name,
                        "value": data.value
                    } for data in result
                ]
            }

    async def get(self):
        result = self.sensorService.get({})
        if not result:
            raise HTTPException(status_code=404, detail=f"No sensor data found")
        return {
                "message": "Data retrieved successfully",
                "data": [
                    {
                        "id": data.id,
                        "timestamp": data.timestamp,
                        "gml_id": data.gml_id,
                        "sensor_name": data.sensor_name,
                        "value": data.value
                    } for data in result
                ]
            }

    def get_router(self):
        return self.router
