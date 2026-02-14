"""
Pytest configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.models import Base, User, Profile, Preference, Interest, Gender
from app.auth import get_password_hash

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with test database"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    from datetime import datetime

    user = User(
        email="test@example.com",
        password_hash=get_password_hash("TestPass123"),
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    profile = Profile(
        user_id=user.id,
        name="Test User",
        date_of_birth=datetime(1995, 6, 15),
        gender=Gender.MALE,
        bio="Test bio",
        onboarding_completed=True,
        profile_completion=50
    )
    db_session.add(profile)
    db_session.flush()

    preferences = Preference(
        profile_id=profile.id,
        min_age=18,
        max_age=35,
        looking_for=[g.value for g in Gender],
        max_distance=50
    )
    db_session.add(preferences)

    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def test_admin(db_session):
    """Create a test admin user"""
    from datetime import datetime

    user = User(
        email="admin@example.com",
        password_hash=get_password_hash("AdminPass123"),
        role="admin",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    profile = Profile(
        user_id=user.id,
        name="Admin User",
        date_of_birth=datetime(1990, 1, 1),
        gender=Gender.OTHER,
        onboarding_completed=True,
        profile_completion=100
    )
    db_session.add(profile)

    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user"""
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPass123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client, test_admin):
    """Get authentication headers for admin user"""
    response = client.post(
        "/auth/login",
        json={
            "email": "admin@example.com",
            "password": "AdminPass123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_interests(db_session):
    """Create sample interests"""
    interests = [
        Interest(name="Hiking", category="sports", icon="🥾"),
        Interest(name="Reading", category="hobbies", icon="📚"),
        Interest(name="Cooking", category="food", icon="🍳"),
    ]
    for interest in interests:
        db_session.add(interest)
    db_session.commit()
    return interests
