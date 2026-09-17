import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import text

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

database_url = os.getenv("DATABASE_URL")

if database_url:
    parsed = urlparse(database_url)
    test_database_url = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            "/darukaa_test",
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )
else:
    raise RuntimeError(
        "DATABASE_URL is not set. Configure it in backend/.env before running tests."
    )

os.environ["DATABASE_URL"] = test_database_url
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _setup_test_database():
    """Create all tables once for the test session, and drop them afterwards.

    Assumes the target database already has the PostGIS extension enabled.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    """Truncate all tables between tests so each test starts clean."""
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
        json={
            "name": "Test User",
            "email": "user@example.com",
            "password": "supersecret123",
        },
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def auth_headers(registered_user):
    token = registered_user["access_token"]
    return {"Authorization": f"Bearer {token}"}


SAMPLE_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [77.5946, 12.9716],
            [77.6046, 12.9716],
            [77.6046, 12.9806],
            [77.5946, 12.9806],
            [77.5946, 12.9716],
        ]
    ],
}
