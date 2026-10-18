from fastapi import HTTPException
from firebase_admin import auth, firestore
from database import get_db_connection as get_db
from services.models import (TokenRequest, RoleRequest,RegisterRequest, 
                             SaveFcmTokenRequest, UpdateLanguageRequest, UpdateProfileRequest)

# FUNCTION: Verify Token

def verify_token(data):

    try:
        decoded_token = auth.verify_id_token(data.token)

        uid = decoded_token["uid"]
        email = decoded_token.get("email")

        # role from firestore
        doc = firestore.client().collection("users").document(uid).get()

        if doc.exists:
            user_data = doc.to_dict()
            role = user_data.get("role", "user")
            name = user_data.get("name")
        else:
            role = "user"
            name = None

        # mySQL user id
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT id
            FROM users
            WHERE firebase_uid = %s AND is_deleted = 0
        """, (uid,))

        mysql_user = cursor.fetchone()

        db.close()

        user_id = mysql_user["id"] if mysql_user else None

        return {
            "status": "success",
            "uid": uid,
            "user_id": user_id,
            "email": email,
            "role": role,
            "name": name
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    

    
# FUNCTION: Set User Role

def set_role(data):

    try:
        # 1. update Firestore
        firestore.client().collection("users").document(data.uid).update({
            "role": data.role
        })

        # 2. update MySQL
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            UPDATE users
            SET role = %s
            WHERE firebase_uid = %s
        """, (data.role, data.uid))

        db.commit()
        db.close()

        return {
            "status": "success",
            "message": "Role updated in both Firestore and MySQL"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




# FUNCTION: User Registration
def register_user(data):
    print("REGISTER HIT:")
    try:
        # 1️⃣ verify token
        decoded = auth.verify_id_token(data.token)
        uid_from_token = decoded["uid"]

        # 2️⃣ تأكيد إن uid مطابق
        if uid_from_token != data.uid:
            raise HTTPException(status_code=401, detail="Invalid token")

        # 3️⃣ connect DB
        db = get_db()
        cursor = db.cursor(dictionary=True)

        # 4️⃣ check if user already exists
        cursor.execute(
            "SELECT id, is_deleted FROM users WHERE firebase_uid = %s",
            (data.uid,)
        )
        existing = cursor.fetchone()

        if existing:
            if existing["is_deleted"] == 1:
                cursor.execute("""
                    UPDATE users
                    SET is_deleted = 0,
                        name = %s,
                        email = %s
                    WHERE firebase_uid = %s
                """, (data.name, data.email, data.uid))

                db.commit()

                return {
                    "status": "reactivated",
                    "message": "User restored"
                }

            db.close()
            return {"status": "exists", "message": "User already registered"}
        # 5️⃣ insert user
        cursor.execute("""
         INSERT INTO users (firebase_uid,name, email,role) 
        VALUES (%s, %s,%s, %s)
        """, (data.uid, data.name, data.email, data.role))

        user_id=cursor.lastrowid

        # بعد INSERT في users
        cursor.execute("""
            INSERT INTO login_logs (firebase_uid, email, action )
            VALUES (%s, %s, %s)
        """, (data.uid, data.email, "signup"))

   
        db.commit()
        db.close()

        return {"status": "success","user_id": user_id ,"message": "User saved in MySQL"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


# FUNCTION: Login Log
def login_log(data: TokenRequest):

    try:
        decoded = auth.verify_id_token(data.token)
        uid = decoded["uid"]
        email = decoded.get("email")

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            SELECT firebase_uid 
            FROM users 
            WHERE firebase_uid = %s AND is_deleted = 0
        """, (uid,))

        check = cursor.fetchone()

        if not check:
            db.close()
            return {"status": "ignored", "message": "User not found"}

        cursor.execute("""
            INSERT INTO login_logs (firebase_uid, email, action)
            VALUES (%s, %s, %s)
        """, (uid, email, "login"))

        db.commit()
        db.close()

        return {"status": "logged"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


# FUNCTION: Update Profile
def update_profile(data):

    try:
        decoded = auth.verify_id_token(data.token)

        uid = decoded["uid"]

        # Update Firestore
        firestore.client().collection("users").document(uid).set({
            "name": data.name,
            "email": data.email
        }, merge=True)

        # Update MySQL
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            UPDATE users
            SET
                name = %s
            WHERE firebase_uid = %s
              AND is_deleted = 0
        """, (
            data.name,
            uid
        ))

        db.commit()
        db.close()

        return {
            "status": "success",
            "message": "Profile updated successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


# FUNCTION: Delete User

def delete_user(data: TokenRequest):
    print("DELETE USER HIT")

    try:
        decoded = auth.verify_id_token(data.token)
        uid = decoded["uid"]
        email = decoded.get("email")

        db = get_db()
        cursor = db.cursor()

        # 1. Soft delete في MySQL (الأهم أولًا)
        cursor.execute("""
            UPDATE users
            SET is_deleted = 1
            email = CONCAT(email, '_deleted_', firebase_uid),
            WHERE firebase_uid = %s
        """, (uid,))

        # 2. log delete في MySQL
        cursor.execute("""
            INSERT INTO login_logs (firebase_uid, email, action)
            VALUES (%s, %s, %s)
        """, (uid, email, "delete")) 

        db.commit()
        db.close()

        firestore.client().collection("users").document(uid).delete()

        # 3. بعد نجاح MySQL → احذفي من Firebase
        print("Deleting user from Firebase Auth...")
        auth.delete_user(uid)
        print("User deleted from Firebase Auth.")

        return {"status": "deleted"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


def purge_deleted_users():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        DELETE FROM users
        WHERE is_deleted = 1
    """)

    db.commit()
    db.close()

    return {"status": "purged"}