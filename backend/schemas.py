from pydantic import BaseModel, EmailStr
from typing import Optional

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class RoleUpdateRequest(BaseModel):
    role: str  # 'department_head' | 'asset_manager'

class EmployeeOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    department_id: Optional[int]

    class Config:
        from_attributes = True