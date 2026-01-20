from sqlalchemy.orm import Session
from app.models.user import User, Call
from datetime import datetime
import uuid
import random


class MatchmakingQueue:
    def __init__(self):
        self.waiting_users = []
    
    def add_user(self, user_id: str, user_data: dict) -> None:
        self.waiting_users.append({
            "user_id": user_id,
            "joined_at": datetime.utcnow(),
            **user_data
        })
    
    def remove_user(self, user_id: str) -> None:
        self.waiting_users = [u for u in self.waiting_users if u["user_id"] != user_id]
    
    def find_match(self, user_id: str, blocked_users: list = None) -> dict | None:
        """Find a match for the user, excluding blocked users"""
        if blocked_users is None:
            blocked_users = []
        
        available_users = [
            u for u in self.waiting_users 
            if u["user_id"] != user_id and u["user_id"] not in blocked_users
        ]
        
        if available_users:
            matched_user = random.choice(available_users)
            self.remove_user(matched_user["user_id"])
            return matched_user
        return None
    
    def get_queue_size(self) -> int:
        return len(self.waiting_users)
    
    def clear(self) -> None:
        self.waiting_users = []


matchmaking_queue = MatchmakingQueue()


def create_call(db: Session, initiator_id: str, receiver_id: str) -> Call:
    call_token = str(uuid.uuid4())
    call = Call(
        initiator_id=initiator_id,
        receiver_id=receiver_id,
        call_token=call_token,
        status="ongoing"
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


def end_call(db: Session, call_id: str) -> Call:
    call = db.query(Call).filter(Call.id == call_id).first()
    if call:
        call.ended_at = datetime.utcnow()
        call.status = "completed"
        if call.ended_at and call.started_at:
            call.duration_seconds = int((call.ended_at - call.started_at).total_seconds())
        db.commit()
        db.refresh(call)
    return call


def get_user_call_history(db: Session, user_id: str, limit: int = 20) -> list:
    calls = db.query(Call).filter(
        (Call.initiator_id == user_id) | (Call.receiver_id == user_id)
    ).order_by(Call.started_at.desc()).limit(limit).all()
    return calls
