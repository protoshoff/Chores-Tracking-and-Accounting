"""Shared fixtures for tests — uses an in-memory SQLite DB."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

from backend.main import app
from backend.db import get_session
from backend.models import User, Chore, Frequency, Settings
from backend.services.pin import hash_pin

# In-memory engine shared across a single test
_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})


def _override_get_session():
    with Session(_engine) as session:
        yield session


# Patch the app's DB dependency
app.dependency_overrides[get_session] = _override_get_session


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test, drop after."""
    SQLModel.metadata.create_all(_engine)
    # Seed a default PIN so auth works
    with Session(_engine) as session:
        session.add(Settings(key="parent_pin", value=hash_pin("1234")))
        session.commit()
    yield
    SQLModel.metadata.drop_all(_engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def seed_kid():
    """Insert a test kid and return their id."""
    with Session(_engine) as session:
        kid = User(name="TestKid", balance=0.0, allowance=10.0, is_active=True)
        session.add(kid)
        session.commit()
        session.refresh(kid)
        return kid.id


@pytest.fixture
def seed_chore(seed_kid):
    """Insert a daily chore for the test kid."""
    with Session(_engine) as session:
        chore = Chore(
            kid_id=seed_kid,
            name="Test Chore",
            frequency=Frequency.DAILY,
            reward=1.0,
        )
        session.add(chore)
        session.commit()
        session.refresh(chore)
        return chore.id
