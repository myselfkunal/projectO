"""WebSocket endpoint for WebRTC signaling"""
from fastapi import APIRouter, WebSocket, Query, Depends, status, Security
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
import json
import logging
from typing import Dict, Set

from app.core.database import get_db
from app.core.security import decode_token, get_current_user
from app.utils.webrtc_service import (
    initialize_webrtc_session,
    relay_offer,
    relay_answer,
    relay_ice_candidate,
    close_webrtc_session,
    webrtc_manager
)
from app.utils.call_service import get_call_by_id
from app.utils.user_service import get_user_by_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])

# Store active WebSocket connections
# Format: {call_id: {user_id: websocket, remote_user_id: websocket}}
active_connections: Dict[str, Dict[str, WebSocket]] = {}


async def get_user_from_token(token: str) -> str | None:
    """Extract user ID from token"""
    if not token:
        return None
    
    if token.startswith("Bearer "):
        token = token[7:]
    
    payload = decode_token(token)
    if payload:
        return payload.get("sub")
    return None


@router.websocket("/webrtc/{call_id}")
async def websocket_webrtc_endpoint(
    websocket: WebSocket,
    call_id: str,
    token: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for WebRTC signaling
    
    Handles:
    - SDP offer/answer exchange
    - ICE candidate relay
    - Connection state management
    - Media stream setup coordination
    """
    
    # Authenticate user
    user_id = await get_user_from_token(token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return
    
    # Verify call exists
    call = get_call_by_id(db, call_id)
    if not call:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Call not found")
        return
    
    # Verify user is part of this call
    if user_id not in [call.initiator_id, call.receiver_id]:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Not part of this call")
        return
    
    # Determine remote user ID
    remote_user_id = call.receiver_id if user_id == call.initiator_id else call.initiator_id
    
    # Accept connection
    await websocket.accept()
    
    # Initialize WebRTC session if not already done
    if call_id not in active_connections:
        active_connections[call_id] = {}
        initialize_webrtc_session(db, call_id)
        # Also create in webrtc_manager for tracking
        webrtc_manager.create_peer_connection(call_id, call.initiator_id, call.receiver_id)
        logger.info(f"New WebRTC session for call {call_id}")
    
    # Store connection
    active_connections[call_id][user_id] = websocket
    
    try:
        # Notify both users that connection is ready
        await broadcast_to_call(
            call_id,
            {
                "type": "connection_ready",
                "user_id": user_id,
                "message": f"User {user_id[:8]}... connected"
            },
            user_id
        )
        
        logger.info(f"User {user_id[:8]}... connected to call {call_id}")
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                logger.debug(f"WebRTC message from {user_id[:8]}...: {message_type}")
                
                if message_type == "offer":
                    # Relay SDP offer to remote user
                    offer = message.get("offer")
                    if relay_offer(call_id, offer):
                        await send_to_user(
                            call_id,
                            remote_user_id,
                            {
                                "type": "offer",
                                "offer": offer,
                                "from": user_id
                            }
                        )
                        logger.info(f"SDP offer relayed in call {call_id}")
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Failed to relay offer"
                        })
                
                elif message_type == "answer":
                    # Relay SDP answer to remote user
                    answer = message.get("answer")
                    if relay_answer(call_id, answer):
                        await send_to_user(
                            call_id,
                            remote_user_id,
                            {
                                "type": "answer",
                                "answer": answer,
                                "from": user_id
                            }
                        )
                        logger.info(f"SDP answer relayed in call {call_id}")
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Failed to relay answer"
                        })
                
                elif message_type == "ice_candidate":
                    # Relay ICE candidate
                    candidate = message.get("candidate")
                    if relay_ice_candidate(call_id, candidate):
                        await send_to_user(
                            call_id,
                            remote_user_id,
                            {
                                "type": "ice_candidate",
                                "candidate": candidate,
                                "from": user_id
                            }
                        )
                        logger.debug(f"ICE candidate relayed in call {call_id}")
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Failed to relay ICE candidate"
                        })
                
                elif message_type == "connection_state":
                    # Send current connection state
                    state = message.get("state")
                    await broadcast_to_call(
                        call_id,
                        {
                            "type": "connection_state",
                            "user_id": user_id,
                            "state": state
                        },
                        user_id
                    )
                    logger.info(f"Connection state updated for {user_id[:8]}...: {state}")
                
                elif message_type == "chat_message":
                    # Relay chat message
                    text = message.get("text")
                    await broadcast_to_call(
                        call_id,
                        {
                            "type": "chat_message",
                            "from": user_id,
                            "text": text,
                            "timestamp": message.get("timestamp")
                        }
                    )
                    logger.debug(f"Chat message relayed in call {call_id}")

                elif message_type == "end_call":
                    # Notify both users and close sockets
                    await broadcast_to_call(
                        call_id,
                        {
                            "type": "call_ended",
                            "user_id": user_id,
                            "message": "Call ended"
                        }
                    )
                    logger.info(f"Call ended by {user_id[:8]}... in call {call_id}")

                    # Close all sockets for this call
                    sockets = list(active_connections.get(call_id, {}).values())
                    for ws in sockets:
                        try:
                            await ws.close(code=1000, reason="Call ended")
                        except Exception:
                            pass
                    break
                
                elif message_type == "ping":
                    # Keep-alive ping
                    await websocket.send_json({"type": "pong"})
                
                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })
            
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
            except Exception as e:
                logger.error(f"Error handling message: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error: {str(e)}"
                })
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id} in call {call_id}: {str(e)}")
    
    finally:
        # Clean up
        if call_id in active_connections:
            if user_id in active_connections[call_id]:
                del active_connections[call_id][user_id]
            
            # If both users disconnected, close the WebRTC session
            if not active_connections[call_id]:
                close_webrtc_session(call_id)
                del active_connections[call_id]
                logger.info(f"WebRTC session closed for call {call_id}")
            else:
                # Notify remaining user
                await broadcast_to_call(
                    call_id,
                    {
                        "type": "user_disconnected",
                        "user_id": user_id
                    }
                )
        
        logger.info(f"User {user_id[:8]}... disconnected from call {call_id}")


async def send_to_user(call_id: str, user_id: str, message: Dict):
    """Send message to a specific user in a call"""
    if call_id in active_connections and user_id in active_connections[call_id]:
        websocket = active_connections[call_id][user_id]
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {str(e)}")


async def broadcast_to_call(call_id: str, message: Dict, exclude_user_id: str = None):
    """Broadcast message to all users in a call"""
    if call_id not in active_connections:
        return
    
    for user_id, websocket in active_connections[call_id].items():
        if exclude_user_id and user_id == exclude_user_id:
            continue
        
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to broadcast to user {user_id}: {str(e)}")


@router.get("/webrtc/connection-state/{call_id}", openapi_extra={"security": [{"Bearer": []}]})
async def get_connection_state(
    call_id: str,
    current_user = Depends(get_current_user)
):
    """Get current WebRTC connection state for debugging"""
    state = webrtc_manager.get_connection_state(call_id)
    if state:
        return state
    
    # If not in manager, check active connections
    if call_id in active_connections:
        return {
            "call_id": call_id,
            "users": list(active_connections[call_id].keys()),
            "user_count": len(active_connections[call_id]),
            "connection_state": "active"
        }
    
    return {"error": "Connection not found", "call_id": call_id}


@router.get("/webrtc/active-connections", openapi_extra={"security": [{"Bearer": []}]})
async def get_active_connections(
    current_user = Depends(get_current_user)
):
    """Get all active WebRTC connections (admin only)"""
    return {
        "total_calls": len(active_connections),
        "connections": {
            call_id: {
                "users": list(users.keys()),
                "user_count": len(users)
            }
            for call_id, users in active_connections.items()
        }
    }
