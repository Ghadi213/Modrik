from database import get_db_connection
from firebase_admin import messaging

def send_message_notification(token: str):

    try:

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT language
            FROM users
            WHERE fcm_token = %s
        """, (token,))

        user = cursor.fetchone()

        language = "en"

        if user and user["language"]:
            language = user["language"]

        # ===== TRANSLATIONS =====

        if language == "ar":

            title = "رسالة جديدة"
            body = "لديك رسالة جديدة"

        else:

            title = "New Message"
            body = "You received a new message."

        # ===== SEND =====

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=token
        )

        messaging.send(message)

        print("Message notification sent")

    except Exception as e:
        print("Notification error:", e)


def send_message(payload: dict):
    """
    Send a chat message
    inside a consultation.
    """

    cursor = None
    conn = None
    try:
        conn = get_db_connection()

        consultation_id = payload.get("consultation_id")
        sender_id = payload.get("sender_id")
        message_text = payload.get("message_text")

        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT user_id, expert_id
            FROM consultations
            WHERE id = %s
        """, (consultation_id,))
        consultation = cursor.fetchone()
        
        if not consultation:
            return {"error": "Consultation not found"}
        

        sender_id = int(payload.get("sender_id"))

        if sender_id == int(consultation["user_id"]):
         sender_role = "user"

        elif sender_id == int(consultation["expert_id"]):
          sender_role = "expert"

        else:
          return {"error": "Sender not allowed in this consultation"}

        cursor.close()  

        # نرجع cursor عادي للـ INSERT
        cursor = conn.cursor()

        query = """
        INSERT INTO messages (
            consultation_id,
            sender_id,
            sender_role,
            message_text
        )
        VALUES (%s, %s, %s, %s)
        """

        values = (
            consultation_id,
            sender_id,
            sender_role,
            message_text
        )

        cursor.execute(query, values)
        conn.commit()

        # ===== DETERMINE RECEIVER =====

        receiver_id = None

        if sender_role == "expert":
            receiver_id = consultation["user_id"]

        else:
            receiver_id = consultation["expert_id"]

        # ===== GET RECEIVER TOKEN =====

        cursor.close()  
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT fcm_token
            FROM users
            WHERE id = %s
        """, (receiver_id,))

        user = cursor.fetchone()

        # ===== SEND NOTIFICATION =====

        if user and user["fcm_token"]:

            send_message_notification(
                user["fcm_token"]
            )

        return {
            "message": "Message sent successfully"
        }

    except Exception as e:
        return {
            "error": str(e)
        }

    finally:
        if cursor :
            cursor.close()
        if conn:
            conn.close()



def get_messages(
    consultation_id: int,
    current_user_id: int,
    current_user_role: str
):
    """
    Get messages securely for one consultation.
    """

    cursor = None
    conn = None
    try:
        conn = get_db_connection()

        cursor = conn.cursor(dictionary=True)

        # =========================
        # CHECK CONSULTATION ACCESS
        # =========================

        if current_user_role == "user":

            query = """
            SELECT id
            FROM consultations
            WHERE id = %s
            AND user_id = %s
            """

            values = (
                consultation_id,
                current_user_id
            )

        else:

            query = """
            SELECT id
            FROM consultations
            WHERE id = %s
            AND expert_id = %s
            """

            values = (
                consultation_id,
                current_user_id
            )

        cursor.execute(query, values)

        consultation = cursor.fetchone()

        # ❌ Unauthorized
        if not consultation:
            return {
                "error": "Unauthorized access"
            }

        # =========================
        # GET MESSAGES
        # =========================

        query = """
        SELECT
            id,
            consultation_id,
            sender_id,
            sender_role,
            message_text,
            sent_at,
            is_read
        FROM messages
        WHERE consultation_id = %s
        ORDER BY sent_at ASC
        """

        cursor.execute(query, (consultation_id,))

        messages = cursor.fetchall()

        return {
            "message": "Messages fetched successfully",
            "messages": messages
        }

    except Exception as e:
        return {
            "error": str(e)
        }

    finally:
       
        if cursor:
            cursor.close()
        if conn:
            conn.close()    