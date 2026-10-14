"""
backend/tests/test_integrations_api.py
--------------------------------------
Integration tests for external business system connectors, manual synchronization,
duplicate prevention, and sync audit logging.
"""

from fastapi.testclient import TestClient
from app.core.config import settings

DEMO_PWD = settings.DEMO_PASSWORD


def get_auth_headers(client: TestClient, username: str = "superstore.admin", company_id: int = 1):
    login_resp = client.post("/api/v1/auth/login", json={"username": username, "password": DEMO_PWD})
    token = login_resp.json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
        "X-Company-ID": str(company_id)
    }


def test_list_integrations(client: TestClient):
    headers = get_auth_headers(client)
    resp = client.get("/api/v1/integrations", headers=headers)
    assert resp.status_code == 200
    connectors = resp.json()
    assert len(connectors) > 0
    first = connectors[0]
    assert "integration_id" in first
    assert "connector_type" in first
    assert "sync_status" in first


def test_create_and_toggle_connector(client: TestClient):
    headers = get_auth_headers(client)
    payload = {
        "name": "Square POS Terminal - Store 2",
        "connector_type": "POS_REST_API",
        "store_id": 2,
        "config": {"terminal_id": "SQ-TRM-8821"}
    }
    create_resp = client.post("/api/v1/integrations", json=payload, headers=headers)
    assert create_resp.status_code == 201
    int_id = create_resp.json()["integration_id"]
    assert create_resp.json()["is_active"] is True

    # Disable connector
    toggle_resp = client.patch(f"/api/v1/integrations/{int_id}/toggle?is_active=false", headers=headers)
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["is_active"] is False

    # Re-enable
    toggle_back = client.patch(f"/api/v1/integrations/{int_id}/toggle?is_active=true", headers=headers)
    assert toggle_back.status_code == 200
    assert toggle_back.json()["is_active"] is True


def test_trigger_reference_connector_sync(client: TestClient):
    headers = get_auth_headers(client)
    # Get active connector
    connectors = client.get("/api/v1/integrations", headers=headers).json()
    active_int = next(c for c in connectors if c["is_active"])
    int_id = active_int["integration_id"]

    # Trigger sync
    sync_resp = client.post(f"/api/v1/integrations/{int_id}/sync", headers=headers)
    assert sync_resp.status_code == 200
    data = sync_resp.json()
    assert data["status"] == "SUCCESS"
    assert data["records_processed"] >= 1
    assert "cursor_checkpoint" in data

    # Check sync logs
    logs_resp = client.get(f"/api/v1/integrations/{int_id}/logs", headers=headers)
    assert logs_resp.status_code == 200
    logs = logs_resp.json()
    assert len(logs) > 0
    assert logs[0]["status"] == "SUCCESS"
