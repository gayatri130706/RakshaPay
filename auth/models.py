from pydantic import BaseModel, EmailStr
from typing import Optional

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class GoogleSigninRequest(BaseModel):
    email: str
    name: Optional[str] = None
    google_id: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user_name: str
    user_email: str

class UserResponse(BaseModel):
    name: str
    email: str
    auth_provider: str
