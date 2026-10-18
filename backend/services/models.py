from pydantic import BaseModel
from typing import Optional, Dict, Any, List

# Request Models
# Token and Role Management

class TokenRequest(BaseModel):
    token: str


class RoleRequest(BaseModel):
    uid: str
    role: str


class RegisterRequest(BaseModel):
    uid: str
    name: str
    email: str
    role: str
    token: str


class UpdateProfileRequest(BaseModel):
    token: str
    name: str


# FCM Token Management

class SaveFcmTokenRequest(BaseModel):
    uid: str
    fcm_token: str


# Language Preference Update

class UpdateLanguageRequest(BaseModel):
    uid: str
    language: str


#  AI REQUEST MODELS

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    analysis_data: Optional[Dict[str, Any]] = None


# Disease Translation Models

class DiseaseRequest(BaseModel):
    disease: str
    language: str


class DiseasesRequest(BaseModel):
    diseases: list[str]


