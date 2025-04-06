from sqlalchemy import text
from sqlmodel import Session
from src.core.db_config import citydb_engine
from fastapi import HTTPException


class CityDBService:
    def generateGrids(self, resolution:int):
        try:
            # will update the lat lon part soon. now just for testing
            sqlSelect = text(""" 
                INSERT INTO citydb.raster (geom, resolution)
                WITH grid AS (
                    SELECT ((ST_SquareGrid(:resolution, ST_Transform(envelope, 4326)))).geom 
                    FROM citydb.cityobject

                )
                SELECT DISTINCT(geom), :resolution
                FROM grid
                RETURNING id, geom, resolution;
            """)

            with Session(citydb_engine) as session:
                result = session.execute(sqlSelect, params={"resolution": resolution}).mappings().all()
                session.commit()
            
            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

    def generateBuilding2GridMappings(self, resolution: int):
        try:
            # will update the lat lon part soon. now just for testing
            sqlSelect = text("""                             
                with building_locations AS (
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

            with Session(citydb_engine) as session:
                result = session.execute(sqlSelect, params={"resolution": resolution}).mappings().all()
                session.commit()
            
            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
        
    def getGridCenters(self, resolution: int):
        try:
            # will update the lat lon part soon. now just for testing
            sqlSelect = text("""
                SELECT g.id AS rasterId, (ST_X(ST_Centroid(g.geom)) / 10000) AS longitude, (ST_Y(ST_Centroid(g.geom)) / 100000) AS latitude
                FROM raster g
                WHERE g.resolution = :resolution
            """)

            with Session(citydb_engine) as session:
                result = session.execute(sqlSelect, params={"resolution": resolution}).mappings().fetchall()
            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

    def getGridCenter(self, buildingId: int, resolution: int):
        try:
            sqlSelect = text("""
                SELECT mapper.building_id, mapper.grid_id, (ST_X(ST_Centroid(g.geom)) / 10000) AS longitude, (ST_Y(ST_Centroid(g.geom)) / 100000) AS latitude
                FROM building_2_raster mapper
                JOIN raster g ON mapper.grid_id = g.id
                WHERE mapper.building_id = :buildingId AND g.resolution = :resolution
            """)

            with Session(citydb_engine) as session:
                result = session.execute(sqlSelect, params={"buildingId": buildingId, "resolution": resolution}).mappings().fetchone()

            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
