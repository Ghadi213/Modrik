from database import get_db_connection as get_db
from firebase_admin import auth



# Get Users Count
def get_users_count():
    try:
        users = auth.list_users()
        return len(users.users)
    except Exception:
        return 0

# FUNCTION: Get Analysis Count
def get_analysis_count():

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM analysis_logs
        WHERE type = 'individual'
    """)
    individual = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM analysis_logs
        WHERE type = 'cross'
    """)
    cross = cursor.fetchone()[0]

    db.close()

    return {
        "individual": individual,
        "cross": cross
    }


# FUNCTION: Get Analysis Stats
def get_analysis_stats():

    db = get_db()
    cursor = db.cursor()

    # success analyses
    cursor.execute("""
        SELECT COUNT(*) 
        FROM analysis_logs
        WHERE status = 'success'
    """)
    success = cursor.fetchone()[0]

    # failed analyses
    cursor.execute("""
        SELECT COUNT(*) 
        FROM analysis_logs
        WHERE status = 'failed'
    """)
    failed = cursor.fetchone()[0]

    db.close()

    return {
        "success": success,
        "failed": failed
    }



def get_experts_statistics():
    """
    Get real-time expert statistics based on consultations table.
    """

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        query = """
        SELECT
            users.id AS expert_id,
            users.name AS expert_name,
            COUNT(CASE 
                    WHEN consultations.status = 'completed' 
                    THEN 1 
                 END) AS completed_consultations_count
        FROM users
        LEFT JOIN consultations 
            ON users.id = consultations.expert_id
        WHERE users.role = 'expert'
        GROUP BY users.id, users.name
        ORDER BY completed_consultations_count DESC;
        """

        cursor.execute(query)
        data = cursor.fetchall()

        return {
            "experts": data
        }

    except Exception as e:
        return {
            "error": str(e)
        }

    finally:
        cursor.close()
        db.close()