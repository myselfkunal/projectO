from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CallBase(BaseModel):
    initiator_id: str
    receiver_id: str


class CallCreate(BaseModel):
    receiver_id: str


class CallResponse(BaseModel):
    id: str
    initiator_id: str
    receiver_id: str
    status: str
    call_token: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: int

    class Config:
        from_attributes = True


class AvailableUserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    profile_picture: Optional[str]
    bio: Optional[str]
    is_online: bool

    class Config:
        from_attributes = True


class CallHistoryResponse(BaseModel):
    id: str
    initiator_id: str
    receiver_id: str
    initiator_username: Optional[str]
    receiver_username: Optional[str]
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: int

    class Config:
        from_attributes = True


class UserOnlineStatusResponse(BaseModel):
    user_id: str
    is_online: bool
    username: str
