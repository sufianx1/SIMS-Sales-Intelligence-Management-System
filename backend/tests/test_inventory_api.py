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


def test_inventory_alerts_include_status_field(client: TestClient):
    headers = get_auth_headers(client)
    resp = client.get("/api/v1/inventory/alerts", headers=headers)
    assert resp.status_code == 200
    alerts = resp.json()
    assert isinstance(alerts, list)
    for a in alerts:
        assert "severity" in a
        assert a["severity"] in ["WARNING", "CRITICAL"]
        assert "status" in a
        assert a["status"] in ["LOW_STOCK", "OUT_OF_STOCK"]
        if a["quantity_on_hand"] == 0:
            assert a["status"] == "OUT_OF_STOCK"
            assert a["severity"] == "CRITICAL"


def test_get_rebalance_recommendations(client: TestClient):
    headers = get_auth_headers(client)
    resp = client.get("/api/v1/inventory/rebalance-recommendations", headers=headers)
    assert resp.status_code == 200
    recs = resp.json()
    assert isinstance(recs, list)
    assert len(recs) > 0

    for r in recs:
        assert "recommendation_id" in r
        assert "from_store_id" in r
        assert "to_store_id" in r
        assert r["from_store_id"] != r["to_store_id"]
        assert r["recommended_transfer_qty"] > 0

        # Strict safety constraint: donor store must never violate its own safety threshold
        assert r["projected_from_qty"] >= r["from_min_threshold"]
        # Recipient store must improve towards its safety threshold
        assert r["projected_to_qty"] > r["to_current_qty"]

        # Explainability fields
        assert len(r["explanation"]) > 10
        assert len(r["why_it_matters"]) > 10
        assert len(r["supporting_calculation"]) > 10
        assert r["status"] == "PROPOSAL"


def test_rebalance_recommendation_and_execution_workflow(client: TestClient):
    headers = get_auth_headers(client)

    # 1. Fetch recommendations
    resp = client.get("/api/v1/inventory/rebalance-recommendations", headers=headers)
    assert resp.status_code == 200
    recs = resp.json()
    assert len(recs) > 0
    rec = recs[0]

    from_sid = rec["from_store_id"]
    to_sid = rec["to_store_id"]
    pid = rec["product_id"]
    transfer_qty = rec["recommended_transfer_qty"]

    # 2. Check initial inventory levels
    from_items = client.get(f"/api/v1/inventory?store_id={from_sid}&search={pid}", headers=headers).json()
    to_items = client.get(f"/api/v1/inventory?store_id={to_sid}&search={pid}", headers=headers).json()
    from_qty_before = from_items[0]["quantity_on_hand"]
    to_qty_before = to_items[0]["quantity_on_hand"]

    # 3. Execute the recommended transfer
    transfer_payload = {
        "from_store_id": from_sid,
        "to_store_id": to_sid,
        "product_id": pid,
        "quantity": transfer_qty,
        "reason": f"Execution of rebalance recommendation {rec['recommendation_id']}"
    }
    t_resp = client.post("/api/v1/inventory/transfer", json=transfer_payload, headers=headers)
    assert t_resp.status_code == 200
    t_data = t_resp.json()
    assert t_data["movement_type"] == "TRANSFER"

    # 4. Confirm inventory levels updated consistently on both stores
    from_items_after = client.get(f"/api/v1/inventory?store_id={from_sid}&search={pid}", headers=headers).json()
    to_items_after = client.get(f"/api/v1/inventory?store_id={to_sid}&search={pid}", headers=headers).json()
    assert from_items_after[0]["quantity_on_hand"] == from_qty_before - transfer_qty
    assert to_items_after[0]["quantity_on_hand"] == to_qty_before + transfer_qty

