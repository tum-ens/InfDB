from src.db.repositories.cityDbRepository import CityDBRepository
from src.schemas.resolution import (
    RESOLUTION_ID_PREFIX,
    RESOLUTION_ID_SUFFIX_LENGTH,
    ResolutionEnum,
)


class CityDBService:
    def __init__(self):
        self.repository = CityDBRepository()

    def generateRasterRelatedTables(self, resolution: ResolutionEnum):
        idPrefix = RESOLUTION_ID_PREFIX[resolution]
        idSuffixLength = RESOLUTION_ID_SUFFIX_LENGTH[resolution]

        self.repository.generateRasterRelatedTables(
            resolution, idPrefix, idSuffixLength
        )

    def getRasterCenters(self, resolution: int):
        return self.repository.getRasterCenters(resolution)

    def getRasterCenter(self, buildingId: int, resolution: int):
        return self.repository.getRasterCenter(buildingId, resolution)
