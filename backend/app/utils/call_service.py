"""Call management service for initiating, accepting, and ending calls"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import Call, User, CallStatus
from datetime import datetime
import secrets
import logging

logger = logging.getLogger(__name__)


def create_call(db: Session, initiator_id: str, receiver_id: str) -> Call:
    """Create a new call record"""
    call_token = secrets.token_urlsafe(32)
    
    call = Call(
        initiator_id=initiator_id,
        receiver_id=receiver_id,
        call_token=call_token,
        status="pending"
    )
    
    db.add(call)
    db.commit()
    db.refresh(call)
    
    logger.info(f"Call created: {initiator_id} -> {receiver_id} (token: {call_token})")
    return call


def get_call_by_token(db: Session, call_token: str) -> Call | None:
    """Get call by token"""
    return db.query(Call).filter(Call.call_token == call_token).first()


def get_call_by_id(db: Session, call_id: str) -> Call | None:
    """Get call by ID"""
    return db.query(Call).filter(Call.id == call_id).first()


def accept_call(db: Session, call_id: str) -> Call:
    """Accept a pending call"""
    call = get_call_by_id(db, call_id)
    if not call:
        raise ValueError("Call not found")
    
    if call.status != "pending":
        raise ValueError(f"Cannot accept call with status: {call.status}")
    
    call.status = "ongoing"
    call.started_at = datetime.utcnow()
    db.commit()
    db.refresh(call)
    
    logger.info(f"Call accepted: {call.id}")
    return call


def reject_call(db: Session, call_id: str) -> Call:
    """Reject a pending call"""
    call = get_call_by_id(db, call_id)
    if not call:
        raise ValueError("Call not found")
    
    if call.status != "pending":
        raise ValueError(f"Cannot reject call with status: {call.status}")
    
    call.status = "rejected"
    call.ended_at = datetime.utcnow()
    db.commit()
    db.refresh(call)

    try:
        cleanup_call_history(db, keep_per_user=10)
    except Exception as e:
        logger.warning(f"Failed to cleanup call history after reject: {str(e)}")
    
    logger.info(f"Call rejected: {call.id}")
    return call


def end_call(db: Session, call_id: str) -> Call:
    """End an ongoing call"""
    call = get_call_by_id(db, call_id)
    if not call:
        raise ValueError("Call not found")
    
    if call.status != "ongoing":
        raise ValueError(f"Cannot end call with status: {call.status}")
    
    call.status = "completed"
    call.ended_at = datetime.utcnow()
    
    # Calculate duration
    if call.started_at:
        duration = (call.ended_at - call.started_at).total_seconds()
        call.duration_seconds = int(duration)
    
    db.commit()
    db.refresh(call)

    try:
        cleanup_call_history(db, keep_per_user=10)
    except Exception as e:
        logger.warning(f"Failed to cleanup call history after end: {str(e)}")
    
    logger.info(f"Call ended: {call.id} (Duration: {call.duration_seconds}s)")
    return call


def get_user_call_history(db: Session, user_id: str, limit: int = 20) -> list[Call]:
    """Get user's recent call history"""
    calls = db.query(Call).filter(
        (Call.initiator_id == user_id) | (Call.receiver_id == user_id)
    ).order_by(
        func.coalesce(Call.ended_at, Call.started_at).desc(),
        Call.started_at.desc(),
        Call.id.desc()
    ).limit(limit).all()
    
    return calls


def cleanup_call_history(db: Session, keep_per_user: int = 10) -> int:
    """Keep only the most recent calls per user, delete older completed/rejected calls."""
    user_ids = [row[0] for row in db.query(User.id).all()]
    if not user_ids:
        return 0

    keep_ids: set[str] = set()
    for user_id in user_ids:
        recent_ids = db.query(Call.id).filter(
            (Call.initiator_id == user_id) | (Call.receiver_id == user_id)
        ).order_by(func.coalesce(Call.ended_at, Call.started_at).desc()).limit(keep_per_user).all()
        keep_ids.update([row[0] for row in recent_ids])

    if not keep_ids:
        return 0

    deleted = db.query(Call).filter(
        ~Call.id.in_(keep_ids),
        Call.status.in_([CallStatus.COMPLETED, CallStatus.REJECTED])
    ).delete(synchronize_session=False)
    if deleted:
        db.commit()
    return deleted


def get_active_call(db: Session, user_id: str) -> Call | None:
    """Get user's active call if any"""
    call = db.query(Call).filter(
        ((Call.initiator_id == user_id) | (Call.receiver_id == user_id)),
        Call.status == "ongoing"
    ).first()
    
    return call


def get_pending_call_for_user(db: Session, user_id: str) -> Call | None:
    """Get pending incoming call for user"""
    call = db.query(Call).filter(
        Call.receiver_id == user_id,
        Call.status == "pending"
    ).first()
    
    return call
