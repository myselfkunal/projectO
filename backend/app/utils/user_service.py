from sqlalchemy.orm import Session
from app.models.user import User, BlockedUser, Report, VerificationToken, LoginOTP
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from datetime import datetime, timedelta


def create_user(db: Session, user_create: UserCreate) -> User:
    hashed_password = get_password_hash(user_create.password)
    db_user = User(
        email=user_create.email,
        username=user_create.username,
        full_name=user_create.full_name,
        hashed_password=hashed_password,
        is_verified=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def update_user(db: Session, user: User, user_update: UserUpdate) -> User:
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def set_user_online(db: Session, user_id: str) -> None:
    user = get_user_by_id(db, user_id)
    if user:
        user.is_online = True
        db.commit()


def set_user_offline(db: Session, user_id: str) -> None:
    user = get_user_by_id(db, user_id)
    if user:
        user.is_online = False
        db.commit()


def verify_user_email(db: Session, user: User) -> None:
    user.is_verified = True
    db.commit()


def is_user_blocked(db: Session, user_id: str, other_user_id: str) -> bool:
    """Check if user_id is blocked by other_user_id"""
    blocked = db.query(BlockedUser).filter(
        BlockedUser.blocker_id == other_user_id,
        BlockedUser.blocked_id == user_id
    ).first()
    return blocked is not None


def block_user(db: Session, blocker_id: str, blocked_id: str) -> BlockedUser:
    blocked_user = BlockedUser(blocker_id=blocker_id, blocked_id=blocked_id)
    db.add(blocked_user)
    db.commit()
    return blocked_user


def unblock_user(db: Session, blocker_id: str, blocked_id: str) -> bool:
    blocked_user = db.query(BlockedUser).filter(
        BlockedUser.blocker_id == blocker_id,
        BlockedUser.blocked_id == blocked_id
    ).first()
    if blocked_user:
        db.delete(blocked_user)
        db.commit()
        return True
    return False


def report_user(db: Session, reporter_id: str, reported_id: str, reason: str, description: str | None) -> Report:
    report = Report(
        reporter_id=reporter_id,
        reported_id=reported_id,
        reason=reason,
        description=description
    )
    db.add(report)
    db.commit()
    return report


def create_verification_token(db: Session, user_id: str, token: str) -> VerificationToken:
    expires_at = datetime.utcnow() + timedelta(hours=24)
    verification_token = VerificationToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    db.add(verification_token)
    db.commit()
    return verification_token


def get_verification_token(db: Session, token: str) -> VerificationToken | None:
    from sqlalchemy.orm import joinedload
    
    result = db.query(VerificationToken).options(
        joinedload(VerificationToken.user)
    ).filter(
        VerificationToken.token == token,
        VerificationToken.is_used == False,
        VerificationToken.expires_at > datetime.utcnow()
    ).first()
    
    return result


def create_login_otp(db: Session, user_id: str, code: str) -> LoginOTP:
    # Invalidate any existing unused OTPs for this user
    db.query(LoginOTP).filter(
        LoginOTP.user_id == user_id,
        LoginOTP.is_used == False
    ).update({LoginOTP.is_used: True})
    db.commit()

    expires_at = datetime.utcnow() + timedelta(minutes=10)
    login_otp = LoginOTP(
        user_id=user_id,
        code=code,
        expires_at=expires_at
    )
    db.add(login_otp)
    db.commit()
    db.refresh(login_otp)
    return login_otp


def get_valid_login_otp(db: Session, user_id: str, code: str) -> LoginOTP | None:
    return db.query(LoginOTP).filter(
        LoginOTP.user_id == user_id,
        LoginOTP.code == code,
        LoginOTP.is_used == False,
        LoginOTP.expires_at > datetime.utcnow()
    ).order_by(LoginOTP.created_at.desc()).first()


def get_available_users(db: Session, current_user_id: str, limit: int = 10) -> list[User]:
    """Get list of online, verified users available for matching (excluding self, blocked, and blockers)"""
    # Get users that current_user has blocked
    blocked_by_me = db.query(BlockedUser.blocked_id).filter(
        BlockedUser.blocker_id == current_user_id
    ).all()
    blocked_ids = [b[0] for b in blocked_by_me]
    
    # Get users that have blocked current_user
    blocked_me = db.query(BlockedUser.blocker_id).filter(
        BlockedUser.blocked_id == current_user_id
    ).all()
    blocker_ids = [b[0] for b in blocked_me]
    
    exclude_ids = [current_user_id] + blocked_ids + blocker_ids
    
    # Get online, verified users excluding the above
    available_users = db.query(User).filter(
        User.is_online == True,
        User.is_verified == True,
        User.is_active == True,
        User.id.notin_(exclude_ids)
    ).limit(limit).all()
    
    return available_users
