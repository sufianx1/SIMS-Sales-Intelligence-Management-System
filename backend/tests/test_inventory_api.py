"""
backend/tests/test_inventory_api.py
-----------------------------------
Integration tests for multi-store inventory management:
Stock listings, manual adjustments, supplier receipts, inter-store transfers,
movement audit trail, low-stock alerts, and CSV exports.
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


def test_list_inventory_company_consolidated(client: TestClient):
    headers = get_auth_headers(client)
    resp = client.get("/api/v1/inventory", headers=headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) > 0
    first = items[0]
    assert "inventory_id" in first
    assert "quantity_on_hand" in first
    assert "valuation" in first
    assert first["status"] in ["IN_STOCK", "LOW_STOCK", "OUT_OF_STOCK"]


def test_list_inventory_store_filtered(client: TestClient):
    headers = get_auth_headers(client)
    resp = client.get("/api/v1/inventory?store_id=1", headers=headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) > 0
    assert all(i["store_id"] == 1 for i in items)


def test_adjust_stock_success(client: TestClient):
    headers = get_auth_headers(client)
    # Get current stock
    inv_list = client.get("/api/v1/inventory?store_id=1&search=SUP-OFF-001", headers=headers).json()
    initial_qty = inv_list[0]["quantity_on_hand"]

    payload = {
        "store_id": 1,
        "product_id": "SUP-OFF-001",
        "quantity_change": 5,
        "reason": "Found misplaced stock during floor audit"
    }
    resp = client.post("/api/v1/inventory/adjust", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["quantity_on_hand"] == initial_qty + 5

    # Check movement was recorded
    mov_resp = client.get("/api/v1/inventory/movements?store_id=1&product_id=SUP-OFF-001", headers=headers)
    assert mov_resp.status_code == 200
    movements = mov_resp.json()
    assert len(movements) > 0
    assert movements[0]["movement_type"] == "ADJUSTMENT"


def test_adjust_stock_prevent_negative(client: TestClient):
    headers = get_auth_headers(client)
    payload = {
        "store_id": 1,
        "product_id": "SUP-OFF-001",
        "quantity_change": -99999,  # Impossible deduction
        "reason": "Illegal excessive shrinkage test"
    }
    resp = client.post("/api/v1/inventory/adjust", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "Cannot adjust inventory below zero" in resp.json()["detail"]


def test_receive_stock_success(client: TestClient):
    headers = get_auth_headers(client)
    payload = {
        "store_id": 1,
        "product_id": "SUP-OFF-001",
        "quantity": 20,
        "unit_cost": 75.00,
        "supplier": "Staples Wholesale Supply",
        "reason": "PO #44892 Intake"
    }
    resp = client.post("/api/v1/inventory/receive", json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["quantity_on_hand"] >= 20


def test_transfer_stock_between_stores(client: TestClient):
    headers = get_auth_headers(client)
    # Get Store 1 stock
    s1_items = client.get("/api/v1/inventory?store_id=1&search=SUP-TEC-001", headers=headers).json()
    s1_qty_before = s1_items[0]["quantity_on_hand"]

    # Transfer 2 units from Store 1 to Store 2
    transfer_payload = {
        "from_store_id": 1,
        "to_store_id": 2,
        "product_id": "SUP-TEC-001",
        "quantity": 2,
        "reason": "Inter-Store Rebalance Test"
    }
    resp = client.post("/api/v1/inventory/transfer", json=transfer_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["movement_type"] == "TRANSFER"
    assert data["from_store_id"] == 1
    assert data["to_store_id"] == 2

    # Verify origin Store 1 decremented by 2
    s1_after = client.get("/api/v1/inventory?store_id=1&search=SUP-TEC-001", headers=headers).json()
    assert s1_after[0]["quantity_on_hand"] == s1_qty_before - 2


def test_transfer_stock_same_store_rejected(client: TestClient):
    headers = get_auth_headers(client)
    payload = {
        "from_store_id": 1,
        "to_store_id": 1,
        "product_id": "SUP-TEC-001",
        "quantity": 1,
        "reason": "Invalid same store transfer"
    }
    resp = client.post("/api/v1/inventory/transfer", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "must be different" in resp.json()["detail"]


def test_transfer_foreign_store_rejected(client: TestClient):
    headers = get_auth_headers(client)
    payload = {
        "from_store_id": 1,
        "to_store_id": 99,  # Foreign store
        "product_id": "SUP-TEC-001",
        "quantity": 1,
        "reason": "Foreign store transfer attempt"
    }
    resp = client.post("/api/v1/inventory/transfer", json=payload, headers=headers)
    assert resp.status_code == 404
    assert "does not belong to active company" in resp.json()["detail"]


def test_inventory_alerts(client: TestClient):
    headers = get_auth_headers(client)
    resp = client.get("/api/v1/inventory/alerts", headers=headers)
    assert resp.status_code == 200
    alerts = resp.json()
    assert isinstance(alerts, list)
    for a in alerts:
        assert a["severity"] in ["WARNING", "CRITICAL"]


def test_inventory_export_csv(client: TestClient):
    headers = get_auth_headers(client)
    resp = client.get("/api/v1/inventory/export", headers=headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    content = resp.text
    assert "Product ID,Product Name,SKU" in content
