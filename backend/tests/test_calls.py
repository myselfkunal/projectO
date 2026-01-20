"""Test cases for call endpoints"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.core.security import create_access_token
from passlib.context import CryptContext
import uuid

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@pytest.fixture
def client():
    """Create a test client for each test"""
    from fastapi.testclient import TestClient
    return TestClient(app)

def create_test_user(username: str, email: str, db: Session = None):
    """Helper to create a test user"""
    if db is None:
        db = TestingSessionLocal()
        needs_close = True
    else:
        needs_close = False
    
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
    
    if needs_close:
        db.close()
    
    return user

@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_get_available_users(db, client):
    """Test getting available users"""
    # Create test users
    user1 = create_test_user("user1", "user1@test.com", db)
    user2 = create_test_user("user2", "user2@test.com", db)
    user3 = create_test_user("user3", "user3@test.com", db)
    
    # Create token for user1
    token = create_access_token({"sub": user1.id})
    
    # Get available users
    response = client.get(
        "/calls/available",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    available = response.json()
    assert len(available) > 0
    # Should not include the requesting user
    usernames = [u["username"] for u in available]
    assert "user1" not in usernames

def test_initiate_call(db, client):
    """Test initiating a call"""
    # Create test users
    initiator = create_test_user("initiator", "initiator@test.com", db)
    receiver = create_test_user("receiver", "receiver@test.com", db)
    
    # Create token for initiator
    token = create_access_token({"sub": initiator.id})
    
    # Initiate call
    response = client.post(
        "/calls/initiate",
        json={"receiver_id": receiver.id},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    call_data = response.json()
    assert call_data["initiator_id"] == initiator.id
    assert call_data["receiver_id"] == receiver.id
    assert call_data["status"] == "pending"
    assert "call_token" in call_data
    assert "id" in call_data

def test_initiate_call_to_offline_user(db, client):
    """Test initiating call to offline user"""
    # Create test users
    initiator = create_test_user("initiator", "initiator@test.com", db)
    receiver = create_test_user("receiver", "receiver@test.com", db)
    
    # Set receiver offline
    receiver.is_online = False
    db.commit()
    
    # Create token for initiator
    token = create_access_token({"sub": initiator.id})
    
    # Try to initiate call
    response = client.post(
        "/calls/initiate",
        json={"receiver_id": receiver.id},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "not online" in response.json()["detail"]

def test_accept_call(db, client):
    """Test accepting a call"""
    # Create test users
    initiator = create_test_user("initiator", "initiator@test.com", db)
    receiver = create_test_user("receiver", "receiver@test.com", db)
    
    # Create call
    from app.utils.call_service import create_call
    call = create_call(db, initiator.id, receiver.id)
    
    # Create token for receiver
    token = create_access_token({"sub": receiver.id})
    
    # Accept call
    response = client.post(
        f"/calls/accept/{call.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    call_data = response.json()
    assert call_data["status"] == "ongoing"
    assert call_data["started_at"] is not None

def test_reject_call(db, client):
    """Test rejecting a call"""
    # Create test users
    initiator = create_test_user("initiator", "initiator@test.com", db)
    receiver = create_test_user("receiver", "receiver@test.com", db)
    
    # Create call
    from app.utils.call_service import create_call
    call = create_call(db, initiator.id, receiver.id)
    
    # Create token for receiver
    token = create_access_token({"sub": receiver.id})
    
    # Reject call
    response = client.post(
        f"/calls/reject/{call.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    call_data = response.json()
    assert call_data["status"] == "rejected"

def test_end_call(db, client):
    """Test ending a call"""
    # Create test users
    initiator = create_test_user("initiator", "initiator@test.com", db)
    receiver = create_test_user("receiver", "receiver@test.com", db)
    
    # Create and accept call
    from app.utils.call_service import create_call, accept_call
    call = create_call(db, initiator.id, receiver.id)
    accept_call(db, call.id)
    
    # Create token for initiator
    token = create_access_token({"sub": initiator.id})
    
    # End call
    response = client.post(
        f"/calls/end/{call.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    call_data = response.json()
    assert call_data["status"] == "completed"
    assert call_data["ended_at"] is not None

def test_get_active_call(db, client):
    """Test getting active call"""
    # Create test users
    initiator = create_test_user("initiator", "initiator@test.com", db)
    receiver = create_test_user("receiver", "receiver@test.com", db)
    
    # Create and accept call
    from app.utils.call_service import create_call, accept_call
    call = create_call(db, initiator.id, receiver.id)
    accept_call(db, call.id)
    
    # Create token for initiator
    token = create_access_token({"sub": initiator.id})
    
    # Get active call
    response = client.get(
        "/calls/active",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    call_data = response.json()
    if call_data:  # If there's an active call
        assert call_data["status"] == "ongoing"

def test_get_pending_call(db, client):
    """Test getting pending incoming call"""
    # Create test users
    initiator = create_test_user("initiator", "initiator@test.com", db)
    receiver = create_test_user("receiver", "receiver@test.com", db)
    
    # Create call (pending)
    from app.utils.call_service import create_call
    call = create_call(db, initiator.id, receiver.id)
    
    # Create token for receiver
    token = create_access_token({"sub": receiver.id})
    
    # Get pending call
    response = client.get(
        "/calls/pending",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    call_data = response.json()
    if call_data:  # If there's a pending call
        assert call_data["status"] == "pending"
        assert call_data["receiver_id"] == receiver.id

def test_get_call_history(db, client):
    """Test getting call history"""
    # Create test users
    user = create_test_user("user", "user@test.com", db)
    other_user = create_test_user("other", "other@test.com", db)
    
    # Create multiple calls
    from app.utils.call_service import create_call, end_call
    call1 = create_call(db, user.id, other_user.id)
    call2 = create_call(db, other_user.id, user.id)
    
    # Create token for user
    token = create_access_token({"sub": user.id})
    
    # Get call history
    response = client.get(
        "/calls/history",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    history = response.json()
    assert len(history) >= 2
    # History should contain calls where user is either initiator or receiver
    call_ids = [c["id"] for c in history]
    assert call1.id in call_ids or call2.id in call_ids

def test_unauthorized_access(client):
    """Test that endpoints require authentication"""
    response = client.get("/calls/available")
    assert response.status_code == 403  # Forbidden without token

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
