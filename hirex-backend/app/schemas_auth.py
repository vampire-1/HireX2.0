# app/schemas_auth.py
from pydantic import BaseModel, EmailStr

class EmailPassword(BaseModel):
    email: EmailStr
    password: str

class RegisterResponse(BaseModel):
    transaction_id: str

class LoginResponse(BaseModel):
    transaction_id: str

class VerifyRequest(BaseModel):
    transaction_id: str
    code: str

class ResendRequest(BaseModel):
    transaction_id: str

class OkResponse(BaseModel):
    ok: bool = True
