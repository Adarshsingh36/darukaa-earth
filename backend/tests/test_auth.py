def test_register_creates_user_and_returns_token(client):
    resp = client.post(
        "/api/auth/register",
        json={"name": "Alice", "email": "alice@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["email"] == "alice@example.com"
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_register_duplicate_email_is_rejected(client):
    payload = {"name": "Alice", "email": "alice@example.com", "password": "password123"}
    first = client.post("/api/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/auth/register", json=payload)
    assert second.status_code == 409


def test_login_with_correct_credentials_succeeds(client, registered_user):
    resp = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "supersecret123"},
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_with_wrong_password_fails(client, registered_user):
    resp = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401


def test_me_requires_authentication(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user_with_valid_token(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@example.com"
