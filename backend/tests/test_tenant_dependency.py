"""
backend/tests/test_tenant_dependency.py
---------------------------------------
Tests verifying tenant context resolution, authorization verification,
and cross-tenant isolation enforcement at the dependency layer.
"""

from fastapi import Depends
from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import get_tenant_context
from app.schemas.auth import TenantContext
from app.core.config import settings

DEMO_PWD = settings.DEMO_PASSWORD

# Register a test route to exercise get_tenant_context directly
@app.get("/api/v1/test/tenant-guard")
def endpoint_tenant_guard(context: TenantContext = Depends(get_tenant_context)):
    return {
        "user_id": context.user_id,
        "company_id": context.company_id,
        "company_name": context.company_name,
        "role_name": context.role_name
    }


def test_tenant_context_success_for_member(client: TestClient):
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "superstore.admin",
        "password": DEMO_PWD
    })
    token = login_resp.json()["access_token"]
    superstore_comp_id = next(c["company_id"] for c in login_resp.json()["user"]["companies"] if c["company_name"] == "Superstore")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Company-ID": str(superstore_comp_id)
    }
    resp = client.get("/api/v1/test/tenant-guard", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_id"] == superstore_comp_id
    assert data["company_name"] == "Superstore"


def test_tenant_context_denied_for_non_member(client: TestClient):
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "superstore.admin",
        "password": DEMO_PWD
    })
    token = login_resp.json()["access_token"]

    # Attempt to access Nike (CompanyID 2)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Company-ID": "2"
    }
    resp = client.get("/api/v1/test/tenant-guard", headers=headers)
    assert resp.status_code == 403
    assert "Access denied" in resp.json()["detail"]


def test_tenant_context_missing_header(client: TestClient):
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "superstore.admin",
        "password": DEMO_PWD
    })
    token = login_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/v1/test/tenant-guard", headers=headers)
    assert resp.status_code == 400
    assert "X-Company-ID header is required" in resp.json()["detail"]


def test_tenant_context_nonexistent_company(client: TestClient):
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "superadmin",
        "password": DEMO_PWD
    })
    token = login_resp.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Company-ID": "999999"
    }
    resp = client.get("/api/v1/test/tenant-guard", headers=headers)
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_platform_admin_can_access_any_valid_company(client: TestClient):
    # Platform Admin can access Nike (CompanyID 2)
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "superadmin",
        "password": DEMO_PWD
    })
    token = login_resp.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Company-ID": "2"
    }
    resp = client.get("/api/v1/test/tenant-guard", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_id"] == 2
    assert data["company_name"] == "Nike"
