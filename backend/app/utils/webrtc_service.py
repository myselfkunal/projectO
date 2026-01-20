"""WebRTC signaling service for managing peer connections"""
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import Call

logger = logging.getLogger(__name__)


class WebRTCPeerConnection:
    """Represents a WebRTC peer connection state"""
    
    def __init__(self, call_id: str, user_id: str, remote_user_id: str):
        self.call_id = call_id
        self.user_id = user_id
        self.remote_user_id = remote_user_id
        self.offer: Optional[Dict] = None
        self.answer: Optional[Dict] = None
        self.ice_candidates: List[Dict] = []
        self.connection_state = "new"  # new, connecting, connected, failed, closed
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def add_ice_candidate(self, candidate: Dict):
        """Add an ICE candidate"""
        self.ice_candidates.append({
            **candidate,
            "added_at": datetime.utcnow().isoformat()
        })
        self.updated_at = datetime.utcnow()
    
    def set_offer(self, offer: Dict):
        """Set the SDP offer"""
        self.offer = offer
        self.connection_state = "connecting"
        self.updated_at = datetime.utcnow()
        logger.info(f"Offer set for call {self.call_id}")
    
    def set_answer(self, answer: Dict):
        """Set the SDP answer"""
        self.answer = answer
        self.connection_state = "connected"
        self.updated_at = datetime.utcnow()
        logger.info(f"Answer set for call {self.call_id}")
    
    def close(self):
        """Close the connection"""
        self.connection_state = "closed"
        self.updated_at = datetime.utcnow()
        logger.info(f"Connection closed for call {self.call_id}")
    
    def is_stale(self, timeout_seconds: int = 3600):
        """Check if connection is stale (inactive for too long)"""
        return (datetime.utcnow() - self.updated_at).total_seconds() > timeout_seconds
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "call_id": self.call_id,
            "user_id": self.user_id,
            "remote_user_id": self.remote_user_id,
            "connection_state": self.connection_state,
            "offer": self.offer,
            "answer": self.answer,
            "ice_candidates_count": len(self.ice_candidates),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class WebRTCSignalingManager:
    """Manages WebRTC signaling for all active calls"""
    
    def __init__(self):
        self.peer_connections: Dict[str, WebRTCPeerConnection] = {}
        self.active_calls: Dict[str, str] = {}  # user_id -> call_id mapping
    
    def create_peer_connection(self, call_id: str, initiator_id: str, receiver_id: str):
        """Create a new peer connection"""
        peer = WebRTCPeerConnection(call_id, initiator_id, receiver_id)
        self.peer_connections[call_id] = peer
        self.active_calls[initiator_id] = call_id
        self.active_calls[receiver_id] = call_id
        logger.info(f"Peer connection created for call {call_id}")
        return peer
    
    def get_peer_connection(self, call_id: str) -> Optional[WebRTCPeerConnection]:
        """Get peer connection by call ID"""
        return self.peer_connections.get(call_id)
    
    def get_peer_connection_for_user(self, user_id: str) -> Optional[WebRTCPeerConnection]:
        """Get peer connection for a user"""
        call_id = self.active_calls.get(user_id)
        if call_id:
            return self.peer_connections.get(call_id)
        return None
    
    def handle_offer(self, call_id: str, offer: Dict) -> bool:
        """Handle SDP offer"""
        peer = self.get_peer_connection(call_id)
        if not peer:
            logger.warning(f"Peer connection not found for call {call_id}")
            return False
        
        peer.set_offer(offer)
        return True
    
    def handle_answer(self, call_id: str, answer: Dict) -> bool:
        """Handle SDP answer"""
        peer = self.get_peer_connection(call_id)
        if not peer:
            logger.warning(f"Peer connection not found for call {call_id}")
            return False
        
        peer.set_answer(answer)
        return True
    
    def handle_ice_candidate(self, call_id: str, candidate: Dict) -> bool:
        """Handle ICE candidate"""
        peer = self.get_peer_connection(call_id)
        if not peer:
            logger.warning(f"Peer connection not found for call {call_id}")
            return False
        
        peer.add_ice_candidate(candidate)
        return True
    
    def close_connection(self, call_id: str):
        """Close a peer connection"""
        peer = self.get_peer_connection(call_id)
        if peer:
            peer.close()
            # Remove from active calls
            if peer.user_id in self.active_calls and self.active_calls[peer.user_id] == call_id:
                del self.active_calls[peer.user_id]
            if peer.remote_user_id in self.active_calls and self.active_calls[peer.remote_user_id] == call_id:
                del self.active_calls[peer.remote_user_id]
            logger.info(f"Peer connection closed for call {call_id}")
    
    def cleanup_stale_connections(self, timeout_seconds: int = 3600):
        """Remove stale connections"""
        stale_calls = [
            call_id for call_id, peer in self.peer_connections.items()
            if peer.is_stale(timeout_seconds)
        ]
        
        for call_id in stale_calls:
            peer = self.peer_connections[call_id]
            if peer.user_id in self.active_calls:
                del self.active_calls[peer.user_id]
            if peer.remote_user_id in self.active_calls:
                del self.active_calls[peer.remote_user_id]
            del self.peer_connections[call_id]
            logger.info(f"Removed stale connection for call {call_id}")
    
    def get_connection_state(self, call_id: str) -> Optional[Dict]:
        """Get connection state for debugging"""
        peer = self.get_peer_connection(call_id)
        if peer:
            return peer.to_dict()
        return None
    
    def get_all_connections(self) -> List[Dict]:
        """Get all active connections"""
        return [peer.to_dict() for peer in self.peer_connections.values()]


# Global WebRTC signaling manager instance
webrtc_manager = WebRTCSignalingManager()


def initialize_webrtc_session(db: Session, call_id: str):
    """Initialize WebRTC session for a call"""
    from app.utils.call_service import get_call_by_id
    
    call = get_call_by_id(db, call_id)
    if not call:
        logger.warning(f"Call {call_id} not found")
        return None
    
    peer = webrtc_manager.create_peer_connection(
        call_id,
        call.initiator_id,
        call.receiver_id
    )
    
    logger.info(f"WebRTC session initialized for call {call_id}")
    return peer


def get_webrtc_peer(call_id: str) -> Optional[WebRTCPeerConnection]:
    """Get WebRTC peer connection"""
    return webrtc_manager.get_peer_connection(call_id)


def relay_offer(call_id: str, offer: Dict) -> bool:
    """Relay SDP offer"""
    success = webrtc_manager.handle_offer(call_id, offer)
    if success:
        logger.info(f"Offer relayed for call {call_id}")
    return success


def relay_answer(call_id: str, answer: Dict) -> bool:
    """Relay SDP answer"""
    success = webrtc_manager.handle_answer(call_id, answer)
    if success:
        logger.info(f"Answer relayed for call {call_id}")
    return success


def relay_ice_candidate(call_id: str, candidate: Dict) -> bool:
    """Relay ICE candidate"""
    success = webrtc_manager.handle_ice_candidate(call_id, candidate)
    if success:
        logger.debug(f"ICE candidate relayed for call {call_id}")
    return success


def close_webrtc_session(call_id: str):
    """Close WebRTC session"""
    webrtc_manager.close_connection(call_id)
    logger.info(f"WebRTC session closed for call {call_id}")


def cleanup_expired_sessions(timeout_seconds: int = 3600):
    """Clean up expired WebRTC sessions"""
    webrtc_manager.cleanup_stale_connections(timeout_seconds)
    logger.info(f"Cleaned up stale WebRTC connections (timeout: {timeout_seconds}s)")
