from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta
import logging
from app.core.database import get_db
from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import create_access_token, get_current_user
from app.schemas.user import (
    UserCreate, LoginRequest, TokenResponse, EmailVerificationRequest,
    EmailVerificationConfirm, UserResponse, LoginOTPResponse, LoginOTPVerifyRequest
)
from app.utils.user_service import (
    create_user, get_user_by_email, authenticate_user, 
    verify_user_email, get_verification_token, set_user_online, set_user_offline,
    create_verification_token, create_login_otp, get_valid_login_otp
)
from app.utils.email import send_verification_email, generate_verification_token, send_login_otp_email, generate_otp_code

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
@limiter.limit(f"{settings.RATE_LIMIT_AUTH}/minute")
async def register(request: Request, user_create: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with rate limiting"""
    logger.info(f"Registration attempt for email: {user_create.email}")
    
    # Validate email domain
    if not user_create.email.endswith("@kiit.ac.in"):
        logger.warning(f"Invalid email domain: {user_create.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only @kiit.ac.in email addresses are allowed"
        )
    
    # Check if email already exists
    existing_user = get_user_by_email(db, user_create.email)
    if existing_user:
        logger.warning(f"Email already registered: {user_create.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create user
    db_user = create_user(db, user_create)
    db.commit()
    
    # Generate and create verification token
    token = generate_verification_token()
    verification_token_obj = create_verification_token(db, db_user.id, token)
    db.commit()
    
    # Send verification email
    email_sent = await send_verification_email(db_user.email, token, db_user.username)
    logger.info(f"User registered successfully: {db_user.email}")
    
    return db_user


@router.post("/verify-email", response_model=TokenResponse)
@limiter.limit(f"{settings.RATE_LIMIT_AUTH}/minute")
async def verify_email(request: Request, verify_data: EmailVerificationConfirm, db: Session = Depends(get_db)):
    """Verify email with token - rate limited"""
    logger.info("Email verification attempt")
    
    verification_token = get_verification_token(db, verify_data.token)
    if not verification_token:
        logger.warning("Invalid or expired verification token used")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    user = verification_token.user
    verify_user_email(db, user)
    verification_token.is_used = True
    db.commit()
    logger.info(f"Email verified for user: {user.email}")
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/login", response_model=LoginOTPResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(f"{settings.RATE_LIMIT_AUTH}/minute")
async def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login user (step 1): validate credentials and send OTP"""
    logger.info(f"Login attempt for email: {login_data.email}")
    
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        logger.warning(f"Failed login attempt for email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_verified:
        logger.warning(f"Login attempt with unverified email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    
    if not user.is_active:
        logger.warning(f"Login attempt for inactive user: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    otp_code = generate_otp_code()
    create_login_otp(db, user.id, otp_code)
    await send_login_otp_email(user.email, otp_code, user.username)

    logger.info(f"OTP sent for login: {login_data.email}")
    return {
        "otp_required": True,
        "message": "OTP sent to your email"
    }


@router.post("/login/verify-otp", response_model=TokenResponse)
@limiter.limit(f"{settings.RATE_LIMIT_AUTH}/minute")
async def verify_login_otp(request: Request, otp_data: LoginOTPVerifyRequest, db: Session = Depends(get_db)):
    """Login user (step 2): verify OTP and issue token"""
    logger.info(f"OTP verification attempt for email: {otp_data.email}")

    user = get_user_by_email(db, otp_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or OTP"
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

    otp = get_valid_login_otp(db, user.id, otp_data.otp)
    if not otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )

    otp.is_used = True
    db.commit()

    set_user_online(db, user.id)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    logger.info(f"Successful OTP login for user: {otp_data.email}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/logout", openapi_extra={"security": [{"Bearer": []}]})
@limiter.limit(f"{settings.RATE_LIMIT_AUTH}/minute")
async def logout(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user and mark offline"""
    set_user_offline(db, current_user.id)
    return {"message": "Logged out"}
