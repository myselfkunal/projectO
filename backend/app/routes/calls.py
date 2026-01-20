from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.utils.matching_service import matchmaking_queue, create_call, end_call, get_user_call_history
from app.utils.user_service import get_user_by_id, is_user_blocked
from app.schemas.user import CallResponse
from typing import Dict, List
import json

router = APIRouter(prefix="/calls", tags=["calls"])

# Store active connections
active_connections: Dict[str, WebSocket] = {}
user_calls: Dict[str, str] = {}  # Maps user_id to call_id


def get_current_user_from_ws(token: str, db: Session):
    """Extract user from WebSocket token"""
    payload = decode_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    user = get_user_by_id(db, user_id)
    if not user or not user.is_verified or not user.is_active:
        return None
    return user


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
