"""
backend/tests/test_auth_api.py
------------------------------
Integration tests for authentication API endpoints (/api/v1/auth)
using official SIMS demo accounts.
"""

from fastapi.testclient import TestClient
from app.core.config import settings

DEMO_PWD = settings.DEMO_PASSWORD


def test_login_success_platform_superadmin(client: TestClient):
    payload = {
        "username": "superadmin",
        "password": DEMO_PWD
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@platform.sims"
    assert data["user"]["is_system_admin"] is True
    # System Admin should have access to all 3 demo companies
    assert len(data["user"]["companies"]) >= 3


def test_login_success_company_admin_by_username(client: TestClient):
    payload = {
        "username": "superstore.admin",
        "password": DEMO_PWD
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "superstore.admin"
    assert data["user"]["is_system_admin"] is False
    company_names = [c["company_name"] for c in data["user"]["companies"]]
    assert "Superstore" in company_names


def test_login_success_company_admin_by_email(client: TestClient):
    payload = {
        "email": "admin@superstore.sims.local",
        "password": DEMO_PWD
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "admin@superstore.sims.local"


def test_login_invalid_password(client: TestClient):
    payload = {
        "username": "superstore.admin",
        "password": "WrongPassword999!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    data = response.json()
    assert "Invalid username/email or password" in data["detail"]


def test_login_unknown_user(client: TestClient):
    payload = {
        "username": "nonexistent_user",
        "password": "AnyPassword123!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401


def test_auth_me_authenticated(client: TestClient):
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "superstore.admin",
        "password": DEMO_PWD
    })
    token = login_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["email"] == "admin@superstore.sims.local"
    assert data["name"] == "Superstore Admin"
    assert len(data["companies"]) > 0


def test_auth_me_unauthorized(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_auth_logout(client: TestClient):
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "superstore.admin",
        "password": DEMO_PWD
    })
    token = login_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    logout_resp = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200
    assert "Successfully logged out" in logout_resp.json()["detail"]
