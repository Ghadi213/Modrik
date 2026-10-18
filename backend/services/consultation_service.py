from datetime import datetime
import json
from database import get_db_connection



def create_consultation(payload: dict):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        user_id = payload.get("user_id")
        report_type = payload.get("type")
        report_data = payload.get("data")
        report_name = payload.get("report_name", "Genetic Report")
        user_question = payload.get("user_question")

        report_data_json = json.dumps(report_data)

        query = """
        INSERT INTO consultations (
            user_id,
            report_type,
            report_name,
            report_data,
            user_question,
            status
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        values = (
            user_id,
            report_type,
            report_name,
            report_data_json,
            user_question,
            "waiting"
        )

        cursor.execute(query, values)
        conn.commit()

        return {"message": "Consultation created successfully"}

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        conn.close()


def get_user_consultations(user_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT
            c.id,
            c.user_id,
            c.expert_id,
            c.report_type,
            c.report_name,
            c.report_data,
            c.user_question,
            c.status,
            c.created_at,
            c.updated_at,
            c.reviewed_at,
            u.name AS expert_name
        FROM consultations c
        LEFT JOIN users u ON c.expert_id = u.id
        WHERE c.user_id = %s
        ORDER BY c.created_at DESC
        """

        cursor.execute(query, (user_id,))
        consultations = cursor.fetchall()

        for c in consultations:
            if c.get("report_data"):
                c["report_data"] = json.loads(c["report_data"])

        return {
            "message": "Consultations fetched successfully",
            "consultations": consultations
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        conn.close()



def get_consultation_by_id(consultation_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT  
            c.id,
            c.user_id,
            c.expert_id,
            c.report_type,
            c.report_name,
            c.report_data,
            c.user_question,
            c.status,
            c.created_at,
            u.name AS expert_name
        FROM consultations c
        LEFT JOIN users u ON c.expert_id = u.id
        WHERE c.id = %s
        """

        cursor.execute(query, (consultation_id,))
        consultation = cursor.fetchone()

        if consultation and consultation.get("report_data"):
            consultation["report_data"] = json.loads(consultation["report_data"])

        return {
            "message": "Consultation fetched successfully",
            "consultation": consultation
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        conn.close()


def get_waiting_consultations():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT
            id,
            user_id,
            report_type,
            report_name,
            report_data,
            user_question,
            status,
            created_at
        FROM consultations
        WHERE status = %s
        ORDER BY created_at DESC
        """

        cursor.execute(query, ("waiting",))
        consultations = cursor.fetchall()

        for c in consultations:
            if c.get("report_data"):
                c["report_data"] = json.loads(c["report_data"])

        return {
            "message": "Waiting consultations fetched successfully",
            "consultations": consultations
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        conn.close()



def accept_consultation(consultation_id: int, expert_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        UPDATE consultations
        SET
            status = %s,
            expert_id = %s,
            reviewed_at = NOW()
        WHERE id = %s
        """

        values = ("active", expert_id, consultation_id)

        cursor.execute(query, values)
        conn.commit()

        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT firebase_uid
            FROM users
            WHERE id = (
                SELECT user_id
                FROM consultations
                WHERE id = %s
            )
        """, (consultation_id,))

        user = cursor.fetchone()

        return {
            "message": "Consultation accepted successfully",
            "firebase_uid": user["firebase_uid"] if user else None
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        conn.close()



def get_active_consultations(expert_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT
            c.id,
            c.user_id,
            c.expert_id,
            c.report_type,
            c.report_name,
            c.report_data,
            c.user_question,
            c.status,
            c.created_at,
            c.reviewed_at,
            u.name AS expert_name
        FROM consultations c
        LEFT JOIN users u ON c.expert_id = u.id
        WHERE c.status = %s
        AND c.expert_id = %s
        ORDER BY c.reviewed_at DESC
        """

        cursor.execute(query, ("active", expert_id))
        consultations = cursor.fetchall()

        for c in consultations:
            if c.get("report_data"):
                c["report_data"] = json.loads(c["report_data"])

        return {
            "message": "Active consultations fetched successfully",
            "consultations": consultations
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        conn.close()



def complete_consultation(consultation_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        UPDATE consultations
        SET
            status = %s,
            report_data = NULL,
            deleted_at = NOW(),
            updated_at = NOW()
        WHERE id = %s
        """

        values = ("completed", consultation_id)

        cursor.execute(query, values)
        conn.commit()

        return {
            "message": "Consultation completed successfully"
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        conn.close()



def get_completed_consultations(expert_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT
            c.id,
            c.user_id,
            c.expert_id,
            c.report_type,
            c.report_name,
            c.status,
            c.created_at,
            c.reviewed_at,
            c.updated_at,
            u.name AS expert_name
        FROM consultations c
        LEFT JOIN users u ON c.expert_id = u.id
        WHERE c.status = %s
        AND c.expert_id = %s
        ORDER BY c.updated_at DESC
        """

        cursor.execute(query, ("completed", expert_id))
        consultations = cursor.fetchall()

        return {
            "message": "Completed consultations fetched successfully",
            "consultations": consultations
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        conn.close()