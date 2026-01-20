from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None


class UserResponse(UserBase):
    id: str
    profile_picture: Optional[str]
    bio: Optional[str]
    is_verified: bool
    is_online: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserProfileResponse(UserResponse):
    pass


class EmailVerificationRequest(BaseModel):
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    token: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class BlockUserRequest(BaseModel):
    user_id: str


class ReportUserRequest(BaseModel):
    user_id: str
    reason: str
    description: Optional[str] = None


class CallResponse(BaseModel):
    id: str
    initiator_id: str
    receiver_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: int
    status: str
    
    class Config:
        from_attributes = True
