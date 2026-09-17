import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/darukaa_test"
)
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.database import Base, SessionLocal, engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _setup_test_database():
    """Create all tables once for the test session, and drop them afterwards.
    Assumes the target database already has the PostGIS extension enabled
    (see tests/README or the CI workflow, which runs `CREATE EXTENSION postgis`)."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    """Truncate all tables between tests so each test starts from a clean slate."""
    yield
    db = SessionLocal()
    try:
        db.execute(
            text("TRUNCATE users, projects, sites, metrics RESTART IDENTITY CASCADE")
        )
        db.commit()
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def registered_user(client):
    resp = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": "user@example.com", "password": "supersecret123"},
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def auth_headers(registered_user):
    token = registered_user["access_token"]
    return {"Authorization": f"Bearer {token}"}


SAMPLE_POLYGON = {
    "type": "Polygon",
    "coordinates": [[
        [77.5946, 12.9716],
        [77.6046, 12.9716],
        [77.6046, 12.9806],
        [77.5946, 12.9806],
        [77.5946, 12.9716],
    ]],
}
