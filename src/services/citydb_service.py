from sqlalchemy import text
from sqlmodel import Session
from src.core.db_config import citydb_engine
from fastapi import HTTPException
from src.schemas.city_object import CityObjectInput

class CityDBService:
    def insertCityObject(self, data: CityObjectInput):
        try:
            objectClassId = data.objectclass_id
            gmlId = data.gmlid
            creationDate = data.creation_date

            # SQL query
            sqlInsert = text("""
                INSERT INTO citydb.cityobject (objectclass_id, gmlid, creation_date)
                VALUES (:objectclass_id, :gmlid, :creation_date)
                RETURNING id
            """)

            # Database session
            with Session(citydb_engine) as session:
                result = session.execute(
                    sqlInsert,
                    {
                        "objectclass_id": objectClassId,
                        "gmlid": gmlId,
                        "creation_date": creationDate
                    }
                )
                newId = result.scalar()
                session.commit()

            return newId

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database insertion failed: {str(e)}")
