"""Calls API routes for initiating, accepting, and managing video calls"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import get_current_user, decode_token
from app.models.user import User
from app.schemas.call import (
    CallCreate, CallResponse, AvailableUserResponse
)
from app.utils.call_service import (
    create_call, accept_call, reject_call, end_call,
    get_call_by_id, get_user_call_history, get_active_call,
    get_pending_call_for_user
)
from app.utils.user_service import (
    get_available_users, get_user_by_id, is_user_blocked
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calls", tags=["calls"])

# Store active WebSocket connections for real-time updates
active_connections: dict[str, list] = {}


@router.get("/available", response_model=list[AvailableUserResponse])
@limiter.limit(f"{settings.RATE_LIMIT_API}/minute")
async def get_available_users_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of available users online and not blocked"""
    try:
        available_users = get_available_users(db, current_user.id, limit=20)
        logger.info(f"User {current_user.username} fetched {len(available_users)} available users")
        return available_users
    except Exception as e:
        logger.error(f"Error fetching available users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching available users"
        )


@router.post("/initiate", response_model=CallResponse)
@limiter.limit(f"{settings.RATE_LIMIT_API}/minute")
async def initiate_call(
    request: Request,
    call_create: CallCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initiate a call to another user"""
    try:
        # Check if receiver exists
        receiver = get_user_by_id(db, call_create.receiver_id)
        if not receiver:
            logger.warning(f"Call initiation failed: Receiver {call_create.receiver_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receiver not found"
            )

        # Check if receiver is online
        if not receiver.is_online:
            logger.warning(f"Call initiation failed: Receiver {receiver.username} is offline")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Receiver is not online"
            )

        # Check if blocked
        if is_user_blocked(db, current_user.id, receiver.id):
            logger.warning(f"Call initiation failed: {current_user.username} is blocked by {receiver.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot call this user"
            )

        # Check if there's already an active call
        active_call = get_active_call(db, current_user.id)
        if active_call:
            logger.warning(f"User {current_user.username} already has an active call")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have an active call"
            )

        # Create the call
        call = create_call(db, current_user.id, call_create.receiver_id)
        logger.info(f"Call initiated: {current_user.username} -> {receiver.username}")
        
        return call

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating call: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error initiating call"
        )


@router.post("/accept/{call_id}", response_model=CallResponse)
@limiter.limit(f"{settings.RATE_LIMIT_API}/minute")
async def accept_call_endpoint(
    request: Request,
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept an incoming call"""
    try:
        call = get_call_by_id(db, call_id)
        if not call:
            logger.warning(f"Call acceptance failed: Call {call_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call not found"
            )

        # Check if current user is the receiver
        if call.receiver_id != current_user.id:
            logger.warning(f"Call acceptance failed: {current_user.username} is not the receiver")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the receiver of this call"
            )

        # Accept the call
        call = accept_call(db, call_id)
        logger.info(f"Call accepted: {call_id}")
        
        return call

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting call: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error accepting call"
        )


@router.post("/reject/{call_id}", response_model=CallResponse)
@limiter.limit(f"{settings.RATE_LIMIT_API}/minute")
async def reject_call_endpoint(
    request: Request,
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject an incoming call"""
    try:
        call = get_call_by_id(db, call_id)
        if not call:
            logger.warning(f"Call rejection failed: Call {call_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call not found"
            )

        # Check if current user is the receiver
        if call.receiver_id != current_user.id:
            logger.warning(f"Call rejection failed: {current_user.username} is not the receiver")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the receiver of this call"
            )

        # Reject the call
        call = reject_call(db, call_id)
        logger.info(f"Call rejected: {call_id}")
        
        return call

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting call: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error rejecting call"
        )


@router.post("/end/{call_id}", response_model=CallResponse)
@limiter.limit(f"{settings.RATE_LIMIT_API}/minute")
async def end_call_endpoint(
    request: Request,
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End an ongoing call"""
    try:
        call = get_call_by_id(db, call_id)
        if not call:
            logger.warning(f"Call end failed: Call {call_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call not found"
            )

        # Check if current user is part of the call
        if call.initiator_id != current_user.id and call.receiver_id != current_user.id:
            logger.warning(f"Call end failed: {current_user.username} is not part of this call")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not part of this call"
            )

        # End the call
        call = end_call(db, call_id)
        logger.info(f"Call ended: {call_id} (Duration: {call.duration_seconds}s)")
        
        return call

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending call: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error ending call"
        )


@router.get("/active", response_model=CallResponse | None)
@limiter.limit(f"{settings.RATE_LIMIT_API}/minute")
async def get_active_call_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active call for current user if any"""
    try:
        call = get_active_call(db, current_user.id)
        if call:
            logger.info(f"User {current_user.username} has active call: {call.id}")
        return call
    except Exception as e:
        logger.error(f"Error fetching active call: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching active call"
        )


@router.get("/pending", response_model=CallResponse | None)
@limiter.limit(f"{settings.RATE_LIMIT_API}/minute")
async def get_pending_call_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get pending incoming call for current user if any"""
    try:
        call = get_pending_call_for_user(db, current_user.id)
        if call:
            logger.info(f"User {current_user.username} has pending call: {call.id}")
        return call
    except Exception as e:
        logger.error(f"Error fetching pending call: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching pending call"
        )


@router.get("/history", response_model=list)
@limiter.limit(f"{settings.RATE_LIMIT_API}/minute")
async def get_call_history_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get call history for current user"""
    try:
        calls = get_user_call_history(db, current_user.id, limit=50)
        logger.info(f"User {current_user.username} fetched call history: {len(calls)} calls")
        
        # Convert to response format with usernames
        history = []
        for call in calls:
            history.append({
                "id": call.id,
                "initiator_id": call.initiator_id,
                "receiver_id": call.receiver_id,
                "initiator_username": call.initiator.username if call.initiator else None,
                "receiver_username": call.receiver.username if call.receiver else None,
                "status": call.status.value if hasattr(call.status, 'value') else str(call.status),
                "started_at": call.started_at,
                "ended_at": call.ended_at,
                "duration_seconds": call.duration_seconds
            })
        
        return history
    except Exception as e:
        logger.error(f"Error fetching call history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching call history"
        )


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time communication"""
    # Verify user with token from query params
    token = websocket.query_params.get("token")
    
    # Get DB session
    from app.core.database import SessionLocal
    db = SessionLocal()
    
    user = get_current_user_from_ws(token, db)
    if not user or user.id != user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        db.close()
        return
    
    await websocket.accept()
    active_connections[user_id] = websocket
    
    try:
        from app.utils.user_service import set_user_online
        set_user_online(db, user_id)
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            message_type = message.get("type")
            
            # Handle different message types
            if message_type == "join_queue":
                # User joins matchmaking queue
                user_data = {
                    "username": user.username,
                    "profile_picture": user.profile_picture
                }
                matchmaking_queue.add_user(user_id, user_data)
                
                # Try to find a match
                blocked_users = [b.blocked_id for b in user.blocked_by]
                matched_user = matchmaking_queue.find_match(user_id, blocked_users)
                
                if matched_user:
                    # Create call
                    call = create_call(db, user_id, matched_user["user_id"])
                    user_calls[user_id] = call.id
                    user_calls[matched_user["user_id"]] = call.id
                    
                    # Notify both users of match
                    if matched_user["user_id"] in active_connections:
                        await active_connections[matched_user["user_id"]].send_json({
                            "type": "match_found",
                            "call_id": call.id,
                            "call_token": call.call_token,
                            "matched_user": {
                                "id": user.id,
                                "username": user.username,
                                "profile_picture": user.profile_picture
                            }
                        })
                    
                    await websocket.send_json({
                        "type": "match_found",
                        "call_id": call.id,
                        "call_token": call.call_token,
                        "matched_user": {
                            "id": matched_user["user_id"],
                            "username": matched_user["username"],
                            "profile_picture": matched_user["profile_picture"]
                        }
                    })
                else:
                    await websocket.send_json({
                        "type": "queue_joined",
                        "queue_position": matchmaking_queue.get_queue_size()
                    })
            
            elif message_type == "leave_queue":
                # User leaves matchmaking queue
                matchmaking_queue.remove_user(user_id)
                await websocket.send_json({"type": "queue_left"})
            
            elif message_type == "webrtc_offer":
                # Relay WebRTC offer
                call_id = user_calls.get(user_id)
                if not call_id:
                    continue
                
                receiver_id = message.get("receiver_id")
                if receiver_id and receiver_id in active_connections:
                    await active_connections[receiver_id].send_json({
                        "type": "webrtc_offer",
                        "offer": message.get("offer"),
                        "sender_id": user_id
                    })
            
            elif message_type == "webrtc_answer":
                # Relay WebRTC answer
                call_id = user_calls.get(user_id)
                if not call_id:
                    continue
                
                receiver_id = message.get("receiver_id")
                if receiver_id and receiver_id in active_connections:
                    await active_connections[receiver_id].send_json({
                        "type": "webrtc_answer",
                        "answer": message.get("answer"),
                        "sender_id": user_id
                    })
            
            elif message_type == "webrtc_ice":
                # Relay ICE candidates
                call_id = user_calls.get(user_id)
                if not call_id:
                    continue
                
                receiver_id = message.get("receiver_id")
                if receiver_id and receiver_id in active_connections:
                    await active_connections[receiver_id].send_json({
                        "type": "webrtc_ice",
                        "candidate": message.get("candidate"),
                        "sender_id": user_id
                    })
            
            elif message_type == "chat_message":
                # Relay chat message
                call_id = user_calls.get(user_id)
                if not call_id:
                    continue
                
                receiver_id = message.get("receiver_id")
                if receiver_id and receiver_id in active_connections:
                    await active_connections[receiver_id].send_json({
                        "type": "chat_message",
                        "message": message.get("message"),
                        "sender_id": user_id,
                        "sender_username": user.username,
                        "timestamp": message.get("timestamp")
                    })
            
            elif message_type == "end_call":
                # End the call
                call_id = user_calls.get(user_id)
                if call_id:
                    end_call(db, call_id)
                    receiver_id = message.get("receiver_id")
                    if receiver_id and receiver_id in active_connections:
                        await active_connections[receiver_id].send_json({
                            "type": "call_ended"
                        })
                    if user_id in user_calls:
                        del user_calls[user_id]
                    if receiver_id and receiver_id in user_calls:
                        del user_calls[receiver_id]
    
    except WebSocketDisconnect:
        # User disconnected
        from app.utils.user_service import set_user_offline
        set_user_offline(db, user_id)
        matchmaking_queue.remove_user(user_id)
        if user_id in active_connections:
            del active_connections[user_id]
        if user_id in user_calls:
            del user_calls[user_id]
    
    finally:
        db.close()


@router.get("/history", response_model=List[CallResponse])
def get_call_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    authorization: str = None
):
    """Get user's call history"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization"
        )

    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    user_id = payload.get("sub")
    user = get_user_by_id(db, user_id)
    if not user or not user.is_verified or not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    calls = get_user_call_history(db, user_id, limit)
    return calls
