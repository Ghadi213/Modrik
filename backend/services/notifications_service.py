from fastapi import HTTPException
from firebase_admin import firestore, messaging
from database import get_db_connection as get_db
from services.models import SaveFcmTokenRequest


# Function to send push notification using FCM
def send_push_notification(uid: str):

    try:

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT fcm_token, language
            FROM users
            WHERE firebase_uid = %s
        """, (uid,))

        user = cursor.fetchone()

        db.close()

        if not user:
            return

        token = user["fcm_token"]

        if not token:
            return

        language = user.get("language", "en")

        # ===== TRANSLATIONS =====

        if language == "ar":

            title = "اكتمل التحليل"
            body = "تم الانتهاء من التحليل بنجاح"

        else:

            title = "Analysis Complete"
            body = "Your analysis has been completed successfully."

        # ===== SEND =====

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=token
        )

        messaging.send(message)

        print("Notification sent")

    except Exception as e:
        print("Notification error:", e)



# Function to fetch consultations notification for a user
def send_accept_notification(uid: str):

    try:

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT fcm_token, language
            FROM users
            WHERE firebase_uid = %s
        """, (uid,))

        user = cursor.fetchone()

        db.close()

        if not user:
            return

        token = user["fcm_token"]

        if not token:
            return

        language = user.get("language", "en")

        # ===== TRANSLATIONS =====

        if language == "ar":

            title = "تم قبول الاستشارة"
            body = "تم قبول طلب الاستشارة الخاص بك"

        else:

            title = "Request Accepted"
            body = "Your consultation request has been accepted."

        # ===== SEND =====

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=token
        )

        messaging.send(message)

        print("Acceptance notification sent")

    except Exception as e:
        print("Notification error:", e)



# FUNCTION: Send Message notification
def save_fcm_token(data: SaveFcmTokenRequest):

    try:

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            UPDATE users
            SET fcm_token = %s
            WHERE firebase_uid = %s
        """, (data.fcm_token, data.uid))

        db.commit()
        db.close()

        return {
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
