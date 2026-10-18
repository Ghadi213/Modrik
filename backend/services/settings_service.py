from fastapi import HTTPException
from database import get_db_connection as get_db

# settings_service: update user settings (language preference)
def update_language(data):

    try:

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            UPDATE users
            SET language = %s
            WHERE firebase_uid = %s
        """, (data.language, data.uid))

        db.commit()
        db.close()

        return {
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
