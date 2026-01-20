from sqlalchemy.orm import Session
from app.models.user import User, BlockedUser, Report, VerificationToken
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
