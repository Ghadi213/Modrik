""" 
File: main.py 
Purpose: Main FastAPI application entry point. 
 
Expected: 
- Accept VCF uploads 
- Run OpenCRAVAT 
- Process results 
- Return analysis 
- Single VCF analysis 
- Cross Mendelian analysis 
- AI Chat endpoint 
- Token verification endpoint 
- Role management endpoint
""" 
 
import os 
import tempfile 
import firebase_admin
from firebase_admin import firestore, messaging
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from pydantic import BaseModel 
from typing import Optional, Dict, Any, List
from services.models import (TokenRequest, RoleRequest, RegisterRequest, 
                             SaveFcmTokenRequest, UpdateLanguageRequest,
                             ChatRequest, DiseaseRequest, DiseasesRequest, UpdateProfileRequest)
 
from services.analysis_service import (analyze_one_vcf,analyze_cross_vcf)
from services.chat_service import generate_chat_reply 
from services.disease_ai_service import translate_disease_name, explain_disease_name
from services.notifications_service import (send_push_notification, send_accept_notification, save_fcm_token)
from services.auth_service import (verify_token, set_role, register_user, login_log, delete_user, update_profile, purge_deleted_users)
from services.settings_service import update_language
from services.health_service import get_system_health 
from services.consultation_service import (create_consultation,get_user_consultations,get_consultation_by_id,get_waiting_consultations, accept_consultation,get_active_consultations,complete_consultation,get_completed_consultations)
from services.states import (get_users_count, get_experts_statistics, get_analysis_count, get_analysis_stats)
from services.messages_service import send_message ,get_messages
from firebase_admin import credentials, auth
from fastapi.middleware.cors import CORSMiddleware
from database import get_db_connection as get_db


app = FastAPI() 
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://172.237.116.141:8003"],  
    allow_methods=["*"],
    allow_headers=["*"],
)


# ANALYSIS PIPELINE
@app.post("/analyze_vcf/")
async def analyze_vcf(
   uid: str = Form(None),
   file: UploadFile = File(...)
):
   try:
       result = await analyze_one_vcf(file)
       if uid:
           send_push_notification(uid)
       db = get_db()
       cursor = db.cursor()
       cursor.execute("""
           INSERT INTO analysis_logs (type, status)
           VALUES (%s, %s)
       """, ("individual", "success"))
       db.commit()
       db.close()
       return result
   except Exception as e:
       db = get_db()
       cursor = db.cursor()
       cursor.execute("""
           INSERT INTO analysis_logs (type, status)
           VALUES (%s, %s)
       """, ("individual", "failed"))
       db.commit()
       db.close()
       raise HTTPException(
           status_code=500,
           detail=str(e)
       )
       
       
@app.post("/analyze_cross/")
async def analyze_cross(
   uid: str = Form(None),
   male_file: UploadFile = File(...),
   female_file: UploadFile = File(...)
):
   try:
       result = await analyze_cross_vcf(
           male_file=male_file,
           female_file=female_file
       )
       if uid:
           send_push_notification(uid)
       db = get_db()
       cursor = db.cursor()
       cursor.execute("""
           INSERT INTO analysis_logs (type, status)
           VALUES (%s, %s)
       """, ("cross", "success"))
       db.commit()
       db.close()
       return result
   except Exception as e:
       db = get_db()
       cursor = db.cursor()
       cursor.execute("""
           INSERT INTO analysis_logs (type, status)
           VALUES (%s, %s)
       """, ("cross", "failed"))
       db.commit()
       db.close()
       raise HTTPException(
           status_code=500,
           detail=str(e)
       )       


@app.post("/chat/")
async def chat_with_ai(req: ChatRequest):

    try:

        messages_as_dict = []

        for msg in req.messages:

            message_dict = {
                "role": msg.role,
                "content": msg.content
            }

            messages_as_dict.append(message_dict)

        reply = generate_chat_reply(
            messages=messages_as_dict,
            analysis_summary=req.analysis_data
        )

        return {
            "reply": reply
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# Endpoint: Translate Disease Name

@app.post("/translate_diseases/")
async def translate_diseases(
    req: DiseasesRequest
):

    translated = {}

    for disease in req.diseases:

        try:

            translated[disease] = (
                translate_disease_name(
                    disease
                )
            )

        except Exception:

            translated[disease] = disease

    return {
        "translations": translated
    }


# Endpoint: Explain Disease

@app.post("/explain_disease/")
async def explain_disease(req: DiseaseRequest):

    try:

        explanation = explain_disease_name(
            req.disease,
            req.language
        )

        return {
            "explanation": explanation
        }

    except Exception as e:

        print("========== ERROR ==========")
        print(e)
        print("===========================")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
        
# Endpoint: System Health
@app.get("/system/health") 
async def system_health(): 
    return get_system_health()


# Endpoint: Get User Consultations
@app.get("/users/{user_id}/consultations")
async def get_user_consultations_api(user_id: int):
    return get_user_consultations(user_id)

# Endpoint: Get Consultations info by ID
@app.get("/consultations/details/{consultation_id}")
async def get_one_consultation(consultation_id: int):
    return get_consultation_by_id(consultation_id)

@app.get("/consultations/waiting")
async def waiting_consultations_api():
    return get_waiting_consultations()


@app.post("/consultations/{consultation_id}/accept")
async def accept_consultation_api(
    consultation_id: int,
    payload: dict
):
    expert_id = payload.get("expert_id")
    result = accept_consultation(
            consultation_id,
            expert_id
        )
    uid = result.get("firebase_uid")
    if uid:
            send_accept_notification(uid)
    return result


@app.get("/consultations/active/{expert_id}")
async def active_consultations_api(expert_id: int):

    return get_active_consultations(expert_id)

@app.post("/consultations/{consultation_id}/mark-complete")
async def complete_consultation_api(
    consultation_id: int
):

    return complete_consultation(
        consultation_id
    )   

@app.get("/consultations/completed/{expert_id}")
async def completed_consultations_api(
    expert_id: int
):

    return get_completed_consultations(
        expert_id
    )

# Endpoint: consultations 
@app.post("/consultations")
async def create_consultation_api(payload: dict):
    return create_consultation(payload)


@app.post("/messages/send")
async def send_message_api(payload: dict):

    return send_message(payload)


@app.get("/messages/{consultation_id}")
async def get_messages_api(
    consultation_id: int,
    current_user_id: int=None,
    current_user_role: str=None
):

    return get_messages(
        consultation_id,
        current_user_id,
        current_user_role
    )


# تشغيل Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)


# Endpoint: Verify Token
@app.post("/verify-token")
async def verify_token_api(data: TokenRequest):
    return verify_token(data)


# Endpoint: Set User Role
@app.post("/set-role")  
async def set_role_api(data: RoleRequest):
    return set_role(data)


# Endpoint: Register User
@app.post("/register")
async def register_user_api(data: RegisterRequest):
    return register_user(data)


# Endpoint: login log
@app.post("/login-log")
async def login_log_api(data: TokenRequest):
    return login_log(data)


@app.post("/update-profile")
async def update_profile_api(data: UpdateProfileRequest):
    return update_profile(data)

# Endpoint: delete user
@app.post("/delete-user")
async def delete_user_api(data: TokenRequest):
    return delete_user(data)


# Endpoint: purge deleted users
@app.post("/purge-users")
def purge_users():
    return purge_deleted_users()


# Endpoint: get analysis counts 
@app.get("/analysis-count")
def analysis_count():
    return get_analysis_count()



# Endpoint: get analysis stats
@app.get("/analysis-stats")
def analysis_stats():
    return get_analysis_stats()


# Endpoint: admin stats - expert statistics
@app.get("/expert-statistics")
def expert_statistics():
    return get_experts_statistics()


# Endpoint: send notification 
@app.post("/send-notification")
def send_notification_api(data: SaveFcmTokenRequest):
    send_push_notification(data.uid)
    return {
        "status": "notification sent"
    }


# Endpoint: send acceptance notification
@app.post("/send-accept-notification")
def send_accept_notification_api(data: SaveFcmTokenRequest):
    send_accept_notification(data.uid)
    return {
        "status": "accept notification sent"
    }


# Endpoint: save FCM token
@app.post("/save-fcm-token")
def save_fcm_token_api(data: SaveFcmTokenRequest):
    return save_fcm_token(data)


# Endpoint: update language preference
@app.post("/update-language")
def update_language_api(data: UpdateLanguageRequest):
    return update_language(data)
