from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.schemas.user import UserResponse, UserUpdate, BlockUserRequest, ReportUserRequest
from app.utils.user_service import (
    get_user_by_id, update_user, block_user, unblock_user, 
    report_user, is_user_blocked
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    """Get current user from JWT token"""
    token = credentials.credentials
    logger.info(f"🔐 Received token: {token[:20]}...")
    payload = decode_token(token)
    
    if not payload:
        logger.error(f"❌ Token decode failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"✅ Token decoded, user_id: {payload.get('sub')}")
    user_id = payload.get("sub")
    user = get_user_by_id(db, user_id)
    
    if not user:
        logger.error(f"❌ User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"✅ User authenticated: {user.email}")
    return user


@router.get(
    "/me",
    response_model=UserResponse,
    openapi_extra={
        "security": [{"Bearer": []}]
    }
)
def get_current_user_profile(current_user: UserResponse = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    openapi_extra={
        "security": [{"Bearer": []}]
    }
)
def update_current_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update current user profile"""
    updated_user = update_user(db, current_user, user_update)
    return updated_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    openapi_extra={
        "security": [{"Bearer": []}]
    }
)
def get_user_profile(
    user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get another user's profile"""
    # Check if current user has blocked this user
    if is_user_blocked(db, user_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot view this user's profile"
        )
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post(
    "/block/{user_id}",
    openapi_extra={
        "security": [{"Bearer": []}]
    }
)
def block_user_endpoint(
    user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Block a user"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot block yourself"
        )
    
    block_user(db, current_user.id, user_id)
    return {"message": "User blocked successfully"}


@router.post(
    "/unblock/{user_id}",
    openapi_extra={
        "security": [{"Bearer": []}]
    }
)
def unblock_user_endpoint(
    user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Unblock a user"""
    success = unblock_user(db, current_user.id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not blocked"
        )
    return {"message": "User unblocked successfully"}


@router.post(
    "/report/{user_id}",
    openapi_extra={
        "security": [{"Bearer": []}]
    }
)
def report_user_endpoint(
    user_id: str,
    report_data: ReportUserRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Report a user"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot report yourself"
        )
    
    report_user(db, current_user.id, user_id, report_data.reason, report_data.description)
    return {"message": "User reported successfully"}
