import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import numpy as np

# Set testing environment variables before importing app
os.environ["ENVIRONMENT"] = "testing"
os.environ["JWT_SECRET"] = "test_secret_key_for_testing_purposes_only_12345"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.utils.security import get_password_hash, create_access_token

# SQLite test engine
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session() -> Generator:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Override get_db dependency
    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def client(db_session) -> Generator:
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def test_user(db_session) -> User:
    user = User(
        name="Alice Enterprise",
        email="alice@documind.enterprise",
        password_hash=get_password_hash("password123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_user_2(db_session) -> User:
    user = User(
        name="Bob Isolation",
        email="bob@documind.enterprise",
        password_hash=get_password_hash("bobpassword123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers_user1(test_user: User) -> dict:
    token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers_user2(test_user_2: User) -> dict:
    token = create_access_token(subject=test_user_2.id)
    return {"Authorization": f"Bearer {token}"}
