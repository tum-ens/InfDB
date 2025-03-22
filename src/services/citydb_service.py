from sqlalchemy import text
from sqlmodel import Session
from src.core.db_config import citydb_engine
from fastapi import HTTPException


class CityDBService:
    def getGridCenters(self):
        try:
            # will update the lat lon part soon. now just for testing
            sqlSelect = text("""
                SELECT (ST_X(ST_Centroid(g.geom)) / 10000) AS longitude, (ST_Y(ST_Centroid(g.geom)) / 100000) AS latitude
                FROM test_grid g
            """)

            with Session(citydb_engine) as session:
                result = session.execute(sqlSelect).mappings().fetchall()
            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

    def getGridCenter(self, buildingId: int):
        try:
            sqlSelect = text("""
                SELECT mapper.building_id, mapper.grid_id, ST_X((ST_Centroid(g.geom))) AS longitude, ST_Y((ST_Centroid(g.geom))) AS latitude
                FROM test_building_grid_map mapper
                JOIN test_grid g ON mapper.grid_id = g.id
                WHERE mapper.building_id = :buildingId
            """)

            with Session(citydb_engine) as session:
                result = session.execute(sqlSelect, params={"buildingId": buildingId}).mappings().fetchone()

            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
