"""
backend/tests/test_business_apis.py
-----------------------------------
Integration tests for core business API endpoints:
Companies, Stores, Customers, Products, and Orders.
"""

import uuid
from datetime import date
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


def test_list_companies(client: TestClient):
    # Platform Admin can see all companies
    admin_headers = get_auth_headers(client, username="superadmin", company_id=1)
    resp = client.get("/api/v1/companies", headers=admin_headers)
    assert resp.status_code == 200
    companies = resp.json()
    assert len(companies) >= 3
    names = [c["company_name"] for c in companies]
    assert "Superstore" in names
    assert "Nike" in names
    assert "Puma" in names


def test_list_stores(client: TestClient):
    headers = get_auth_headers(client, username="superstore.admin", company_id=1)
    resp = client.get("/api/v1/stores", headers=headers)
    assert resp.status_code == 200
    stores = resp.json()
    assert len(stores) >= 3
    assert all(s["company_id"] == 1 for s in stores)


def test_customer_crud_and_metrics(client: TestClient):
    headers = get_auth_headers(client, username="superstore.admin", company_id=1)

    # 1. List customers
    list_resp = client.get("/api/v1/customers?limit=10", headers=headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert "items" in data
    assert data["total"] > 0
    first_cust = data["items"][0]
    assert "customer_id" in first_cust
    assert first_cust["company_id"] == 1

    # 2. Get customer detail
    cust_id = first_cust["customer_id"]
    detail_resp = client.get(f"/api/v1/customers/{cust_id}", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["customer"]["customer_id"] == cust_id
    assert "recent_orders" in detail

    # 3. Create a new test customer
    new_id = f"TC-{uuid.uuid4().hex[:6]}"
    create_payload = {
        "customer_id": new_id,
        "customer_name": "Acme Test Corp",
        "segment": "Corporate"
    }
    create_resp = client.post("/api/v1/customers", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    assert create_resp.json()["customer_id"] == new_id

    # 4. Update customer
    update_payload = {"customer_name": "Acme Global Enterprise"}
    update_resp = client.put(f"/api/v1/customers/{new_id}", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["customer_name"] == "Acme Global Enterprise"


def test_product_crud_and_catalog(client: TestClient):
    headers = get_auth_headers(client, username="superstore.admin", company_id=1)

    # 1. List products
    list_resp = client.get("/api/v1/products?limit=10", headers=headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] > 0
    first_prod = data["items"][0]
    assert first_prod["company_id"] == 1

    # 2. Detail
    prod_id = first_prod["product_id"]
    detail_resp = client.get(f"/api/v1/products/{prod_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["product"]["product_id"] == prod_id

    # 3. Create new product
    new_sku = f"TS-{uuid.uuid4().hex[:6]}"
    create_payload = {
        "product_id": new_sku,
        "product_name": "Ultra Ergonomic Desk",
        "category": "Furniture",
        "sub_category": "Tables"
    }
    create_resp = client.post("/api/v1/products", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    assert create_resp.json()["product_id"] == new_sku


def test_order_lifecycle_and_transaction(client: TestClient):
    headers = get_auth_headers(client, username="superstore.admin", company_id=1)

    # 1. Query existing customer and product for Superstore
    cust_resp = client.get("/api/v1/customers?limit=1", headers=headers)
    cust_id = cust_resp.json()["items"][0]["customer_id"]

    prod_resp = client.get("/api/v1/products?limit=1", headers=headers)
    prod_id = prod_resp.json()["items"][0]["product_id"]

    store_resp = client.get("/api/v1/stores", headers=headers)
    store_id = store_resp.json()[0]["store_id"]

    # 2. Create Order with lines in transaction
    order_code = f"TEST-ORD-{int(date.today().strftime('%Y%m%d'))}-01"
    create_payload = {
        "order_id": order_code,
        "order_date": str(date.today()),
        "ship_date": str(date.today()),
        "ship_mode": "First Class",
        "customer_id": cust_id,
        "store_id": store_id,
        "country": "United States",
        "city": "San Francisco",
        "state": "California",
        "postal_code": "94103",
        "region": "West",
        "lines": [
            {
                "product_id": prod_id,
                "quantity": 3,
                "sales": 450.00,
                "discount": 0.05,
                "profit": 120.00
            }
        ]
    }
    order_resp = client.post("/api/v1/orders", json=create_payload, headers=headers)
    assert order_resp.status_code == 201
    data = order_resp.json()
    assert data["order"]["order_id"] == order_code
    assert data["order"]["total_sales"] == 450.00
    assert len(data["lines"]) == 1
    assert data["lines"][0]["product_id"] == prod_id

    # 3. Retrieve order
    get_resp = client.get(f"/api/v1/orders/{order_code}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["order"]["city"] == "San Francisco"

    # 4. Clean up / Delete order
    del_resp = client.delete(f"/api/v1/orders/{order_code}", headers=headers)
    assert del_resp.status_code == 200

    # 5. Verify deleted
    get_after = client.get(f"/api/v1/orders/{order_code}", headers=headers)
    assert get_after.status_code == 404


def test_explainable_insights_endpoint(client: TestClient):
    headers = get_auth_headers(client, username="superstore.admin", company_id=1)
    resp = client.get("/api/v1/analytics/insights", headers=headers)
    assert resp.status_code == 200
    insights = resp.json()
    assert isinstance(insights, list)
    assert len(insights) > 0
    for ins in insights:
        assert "insight_id" in ins
        assert "category" in ins
        assert ins["severity"] in ("CRITICAL", "WARNING", "INFO")
        assert len(ins["explanation"]) > 0
        assert "supporting_data" in ins
        assert "limitations" in ins
        assert "recommended_action" in ins
