from sqlalchemy import text
from sqlmodel import Session
from src.core.dbConfig import citydb_engine
from fastapi import HTTPException

# in this repository we have to write our sqls by hand instead of using ORM tools
# sql codes can be removed to a var in sql file and then be imported here as well.
class CityDBRepository:
    def generateRasterRelatedTables(self, resolution: int):
        with Session(citydb_engine) as session:
            try:
                rasters = self._generateRasters(session, resolution)
                mappings = self._generateBuilding2RasterMappings(session, resolution)
                session.commit()
                return {"rasters": rasters, "mappings": mappings}
            except Exception as e:
                session.rollback()
                raise HTTPException(status_code=500, detail=f"Transaction failed: {str(e)}")

    ##Important information regarding our dataset:
    ##currently we keep citydb data in 4326 SRID format. it returns us lat and lon in meters not in degrees.
    ##to return it to degrees, we've used ST_Transform(ST_SetSRID(g.geom, 25832), 4326) which is POSTGIS method.
    ##This can be updated in the future.
    def getRasterCenters(self, resolution: int):
        try:
            # will update the lat lon part soon. now just for testing
            sqlSelect = text("""
                SELECT g.id AS rasterId, ST_X(ST_Centroid(ST_Transform(ST_SetSRID(g.geom, 25832), 4326))) AS longitude, ST_Y(ST_Centroid(ST_Transform(ST_SetSRID(g.geom, 25832), 4326))) AS latitude
                FROM raster g
                WHERE g.resolution = :resolution
            """)

            with Session(citydb_engine) as session:
                result = session.execute(sqlSelect, params={"resolution": resolution}).mappings().fetchall()
            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

    def getRasterCenter(self, buildingId: int, resolution: int):
        try:
            sqlSelect = text("""
                SELECT mapper.building_id, mapper.raster_id, ST_X(ST_Centroid(ST_Transform(ST_SetSRID(g.geom, 25832), 4326))) AS longitude, ST_Y(ST_Centroid(ST_Transform(ST_SetSRID(g.geom, 25832), 4326))) AS latitude
                FROM building_2_raster mapper
                JOIN raster g ON mapper.raster_id = g.id
                WHERE mapper.building_id = :buildingId AND g.resolution = :resolution
            """)

            with Session(citydb_engine) as session:
                result = session.execute(sqlSelect, params={"buildingId": buildingId, "resolution": resolution}).mappings().fetchone()

            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
        
    def _generateRasters(self, session: Session, resolution: int):
        sql = text("""
            INSERT INTO citydb.raster (geom, resolution)
            WITH grid AS (
                SELECT ((ST_SquareGrid(:resolution, ST_Transform(envelope, 4326)))).geom 
                FROM citydb.cityobject
            )
            SELECT DISTINCT(geom), :resolution
            FROM grid
            RETURNING id, geom, resolution;
        """)
        return session.execute(sql, {"resolution": resolution}).mappings().all()

    def _generateBuilding2RasterMappings(self, session: Session, resolution: int):
        sql = text("""
            WITH building_locations AS (
                SELECT b.id AS building_id,
                       ST_SetSRID(ST_Centroid(c.envelope), 4326) AS geom
                FROM citydb.building b
                JOIN citydb.cityobject c ON b.id = c.id
            )
            INSERT INTO citydb.building_2_raster (building_id, grid_id)
            SELECT p.building_id,
                   (
                       SELECT g.id
                       FROM citydb.raster g
                       WHERE ST_Within(p.geom, g.geom) AND resolution = :resolution
                       LIMIT 1
                   ) AS grid_id
            FROM building_locations p
            RETURNING building_id, grid_id;
        """)
        return session.execute(sql, {"resolution": resolution}).mappings().all()
