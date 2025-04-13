from src.db.repositories.cityDbRepository import CityDBRepository


class CityDBService:
    def __init__(self):
        self.repository = CityDBRepository()

    def generateRasterRelatedTables(self, resolution: int):
        self.repository.generateRasterRelatedTables(resolution)

    def getRasterCenters(self, resolution: int):
        return self.repository.getRasterCenters(resolution)

    def getRasterCenter(self, buildingId: int, resolution: int):
        return self.repository.getRasterCenter(buildingId, resolution)
