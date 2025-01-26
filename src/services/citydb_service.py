from sqlalchemy import text
from sqlmodel import Session
from src.core.db_config import citydb_engine
from fastapi import HTTPException


class CityDBService:
    def get(self, gmlId: str):
        try:
            sqlSelect = text("""
                SELECT id, objectclass_id, gmlid, creation_date
                FROM citydb.cityobject
                WHERE gmlid = :gmlId
            """)

            with Session(citydb_engine) as session:
                result = session.execute(sqlSelect, params={"gmlId": gmlId}).mappings().fetchone()

            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
