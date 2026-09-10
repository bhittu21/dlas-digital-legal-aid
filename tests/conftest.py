import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserRole
from app.services.auth_service import get_password_hash, create_access_token
from app.services.seed_service import seed_database

# Isolated in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    seed_database(session)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def dlao_token(db: Session) -> str:
    user = db.query(User).filter(User.role == UserRole.DLAO_OFFICER).first()
    return create_access_token({"sub": user.email, "role": user.role, "user_id": user.id})


@pytest.fixture
def dlao_headers(dlao_token: str) -> dict:
    return {"Authorization": f"Bearer {dlao_token}"}


@pytest.fixture
def lawyer_token(db: Session) -> str:
    user = db.query(User).filter(User.role == UserRole.PANEL_LAWYER).first()
    return create_access_token({"sub": user.email, "role": user.role, "user_id": user.id})


@pytest.fixture
def lawyer_headers(lawyer_token: str) -> dict:
    return {"Authorization": f"Bearer {lawyer_token}"}


@pytest.fixture
def applicant_token(db: Session) -> str:
    user = db.query(User).filter(User.role == UserRole.APPLICANT).first()
    return create_access_token({"sub": user.email, "role": user.role, "user_id": user.id})


@pytest.fixture
def applicant_headers(applicant_token: str) -> dict:
    return {"Authorization": f"Bearer {applicant_token}"}


@pytest.fixture
def ai_token(db: Session) -> str:
    user = db.query(User).filter(User.role == UserRole.SYSTEM_AI).first()
    return create_access_token({"sub": user.email, "role": user.role, "user_id": user.id})


@pytest.fixture
def ai_headers(ai_token: str) -> dict:
    return {"Authorization": f"Bearer {ai_token}"}
