"""Simplified call endpoint tests"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker, Session
from app.core.database import Base, get_db
from app.models.user import User
from app.core.security import create_access_token
from app.utils.call_service import create_call, accept_call, reject_call, end_call
from passlib.context import CryptContext
import uuid

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_test_user(username: str, email: str, db: Session):
    """Helper to create a test user"""
    user = User(
        id=str(uuid.uuid4()),
        username=username,
        email=email,
        full_name=f"Test {username}",
        hashed_password=pwd_context.hash("testpass123"),
        is_verified=True,
        is_active=True,
        is_online=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def test_create_call(db):
    """Test creating a call"""
    user1 = create_test_user("user1", "user1@test.com", db)
    user2 = create_test_user("user2", "user2@test.com", db)
    
    call = create_call(db, user1.id, user2.id)
    
    assert call.initiator_id == user1.id
    assert call.receiver_id == user2.id
    assert call.status.value == "pending"
    assert call.call_token is not None


def test_accept_call(db):
    """Test accepting a call"""
    user1 = create_test_user("user1", "user1@test.com", db)
    user2 = create_test_user("user2", "user2@test.com", db)
    
    call = create_call(db, user1.id, user2.id)
    assert call.status.value == "pending"
    
    accepted_call = accept_call(db, call.id)
    assert accepted_call.status.value == "ongoing"
    assert accepted_call.started_at is not None


def test_reject_call(db):
    """Test rejecting a call"""
    user1 = create_test_user("user1", "user1@test.com", db)
    user2 = create_test_user("user2", "user2@test.com", db)
    
    call = create_call(db, user1.id, user2.id)
    rejected_call = reject_call(db, call.id)
    
    assert rejected_call.status.value == "rejected"


def test_end_call(db):
    """Test ending a call"""
    user1 = create_test_user("user1", "user1@test.com", db)
    user2 = create_test_user("user2", "user2@test.com", db)
    
    call = create_call(db, user1.id, user2.id)
    accepted_call = accept_call(db, call.id)
    ended_call = end_call(db, call.id)
    
    assert ended_call.status.value == "completed"
    assert ended_call.ended_at is not None
    assert ended_call.duration_seconds >= 0


def test_call_workflow(db):
    """Test full call workflow"""
    user1 = create_test_user("initiator", "initiator@test.com", db)
    user2 = create_test_user("receiver", "receiver@test.com", db)
    
    # Create call
    call = create_call(db, user1.id, user2.id)
    assert call.status.value == "pending"
    
    # Accept call
    call = accept_call(db, call.id)
    assert call.status.value == "ongoing"
    
    # End call
    call = end_call(db, call.id)
    assert call.status.value == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
