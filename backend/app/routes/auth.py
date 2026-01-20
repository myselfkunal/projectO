from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.user import (
    UserCreate, LoginRequest, TokenResponse, EmailVerificationRequest,
    EmailVerificationConfirm, UserResponse
)
from app.utils.user_service import (
    create_user, get_user_by_email, authenticate_user, 
    verify_user_email, get_verification_token
)
from app.utils.email import send_verification_email, generate_verification_token
from app.utils.user_service import create_verification_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Validate email domain
    if not user_create.email.endswith("@kiit.ac.in"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only @kiit.ac.in email addresses are allowed"
        )
    
    # Check if email already exists
    existing_user = get_user_by_email(db, user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create user
    db_user = create_user(db, user_create)
    db.commit()  # Ensure user is saved
    
    # Generate and create verification token
    token = generate_verification_token()
    verification_token_obj = create_verification_token(db, db_user.id, token)
    db.commit()  # Ensure token is saved
    
    # Send verification email (for testing, token is printed to logs)
    email_sent = await send_verification_email(db_user.email, token, db_user.username)
    # Don't fail if email sending fails - token is in database for testing
    
    return db_user


@router.post("/verify-email", response_model=TokenResponse)
async def verify_email(verify_data: EmailVerificationConfirm, db: Session = Depends(get_db)):
    """Verify email with token"""
    verification_token = get_verification_token(db, verify_data.token)
    if not verification_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    user = verification_token.user
    verify_user_email(db, user)
    verification_token.is_used = True
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login user"""
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }
