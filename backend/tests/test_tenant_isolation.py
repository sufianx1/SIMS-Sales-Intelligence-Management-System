"""
backend/tests/test_tenant_isolation.py
--------------------------------------
Mandatory negative security tests proving zero cross-tenant data leakage.
Adversarial test cases verifying that Superstore, Nike, and Puma cannot read,
update, or reference records belonging to each other under any circumstance.
"""

from datetime import date
from fastapi.testclient import TestClient
from app.core.config import settings

DEMO_PWD = settings.DEMO_PASSWORD


def get_token(client: TestClient, username: str = "superstore.admin") -> str:
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": DEMO_PWD})
    return resp.json()["access_token"]


def test_cross_tenant_customer_access_blocked(client: TestClient):
    """
    TEST-ISO-01: Proves Superstore Admin (Company 1) cannot read a customer belonging to Nike (Company 2).
    """
    nike_token = get_token(client, username="nike.admin")
    nike_headers = {"Authorization": f"Bearer {nike_token}", "X-Company-ID": "2"}
    nike_cust_resp = client.get("/api/v1/customers?limit=1", headers=nike_headers)
    assert nike_cust_resp.status_code == 200
    nike_cust_id = nike_cust_resp.json()["items"][0]["customer_id"]

    # Now Superstore Admin attempts to read Nike's customer
    superstore_token = get_token(client, username="superstore.admin")
    superstore_headers = {"Authorization": f"Bearer {superstore_token}", "X-Company-ID": "1"}

    leak_resp = client.get(f"/api/v1/customers/{nike_cust_id}", headers=superstore_headers)
    assert leak_resp.status_code == 404
    assert "not found in this company" in leak_resp.json()["detail"]


def test_cross_tenant_product_access_blocked(client: TestClient):
    """
    TEST-ISO-02: Proves Superstore Admin (Company 1) cannot read a product belonging to Nike (Company 2).
    """
    nike_token = get_token(client, username="nike.admin")
    nike_headers = {"Authorization": f"Bearer {nike_token}", "X-Company-ID": "2"}
    nike_prod_resp = client.get("/api/v1/products?limit=1", headers=nike_headers)
    assert nike_prod_resp.status_code == 200
    nike_prod_id = nike_prod_resp.json()["items"][0]["product_id"]

    # Superstore Admin attempts to view Nike's product
    superstore_token = get_token(client, username="superstore.admin")
    superstore_headers = {"Authorization": f"Bearer {superstore_token}", "X-Company-ID": "1"}

    leak_resp = client.get(f"/api/v1/products/{nike_prod_id}", headers=superstore_headers)
    assert leak_resp.status_code == 404
    assert "not found in this company" in leak_resp.json()["detail"]


def test_cross_tenant_order_access_blocked(client: TestClient):
    """
    TEST-ISO-03: Proves Superstore Admin (Company 1) cannot view an order belonging to Nike (Company 2).
    """
    nike_token = get_token(client, username="nike.admin")
    nike_headers = {"Authorization": f"Bearer {nike_token}", "X-Company-ID": "2"}
    nike_order_resp = client.get("/api/v1/orders?limit=1", headers=nike_headers)
    assert nike_order_resp.status_code == 200
    nike_order_id = nike_order_resp.json()["items"][0]["order_id"]

    # Superstore Admin attempts to view Nike's order
    superstore_token = get_token(client, username="superstore.admin")
    superstore_headers = {"Authorization": f"Bearer {superstore_token}", "X-Company-ID": "1"}

    leak_resp = client.get(f"/api/v1/orders/{nike_order_id}", headers=superstore_headers)
    assert leak_resp.status_code == 404
    assert "not found in this company" in leak_resp.json()["detail"]


def test_cross_tenant_order_creation_with_foreign_customer_rejected(client: TestClient):
    """
    TEST-ISO-04: Proves Superstore cannot create an order referencing Nike's customer.
    """
    # 1. Fetch Nike's customer
    nike_token = get_token(client, username="nike.admin")
    nike_headers = {"Authorization": f"Bearer {nike_token}", "X-Company-ID": "2"}
    nike_cust_id = client.get("/api/v1/customers?limit=1", headers=nike_headers).json()["items"][0]["customer_id"]

    # 2. Fetch Superstore's product
    superstore_token = get_token(client, username="superstore.admin")
    superstore_headers = {"Authorization": f"Bearer {superstore_token}", "X-Company-ID": "1"}
    superstore_prod_id = client.get("/api/v1/products?limit=1", headers=superstore_headers).json()["items"][0]["product_id"]

    # 3. Attempt to create order in Superstore with Nike's customer
    illegal_payload = {
        "order_id": "ILLEGAL-ORD-001",
        "order_date": str(date.today()),
        "customer_id": nike_cust_id,  # Foreign Customer!
        "lines": [
            {
                "product_id": superstore_prod_id,
                "quantity": 1,
                "sales": 100.0,
                "discount": 0.0,
                "profit": 20.0
            }
        ]
    }
    resp = client.post("/api/v1/orders", json=illegal_payload, headers=superstore_headers)
    assert resp.status_code == 400
    assert "Cross-Tenant Violation" in resp.json()["detail"]
    assert "does not belong to active company" in resp.json()["detail"]


def test_cross_tenant_order_creation_with_foreign_store_rejected(client: TestClient):
    """
    TEST-ISO-05: Proves Superstore cannot create an order referencing Nike's store.
    """
    # 1. Fetch Nike's store ID
    nike_token = get_token(client, username="nike.admin")
    nike_headers = {"Authorization": f"Bearer {nike_token}", "X-Company-ID": "2"}
    nike_store_id = client.get("/api/v1/stores", headers=nike_headers).json()[0]["store_id"]

    # 2. Fetch Superstore's customer & product
    superstore_token = get_token(client, username="superstore.admin")
    superstore_headers = {"Authorization": f"Bearer {superstore_token}", "X-Company-ID": "1"}
    superstore_cust_id = client.get("/api/v1/customers?limit=1", headers=superstore_headers).json()["items"][0]["customer_id"]
    superstore_prod_id = client.get("/api/v1/products?limit=1", headers=superstore_headers).json()["items"][0]["product_id"]

    # 3. Attempt to create order in Superstore with Nike's store
    illegal_payload = {
        "order_id": "ILLEGAL-ORD-002",
        "order_date": str(date.today()),
        "customer_id": superstore_cust_id,
        "store_id": nike_store_id,  # Foreign Store!
        "lines": [
            {
                "product_id": superstore_prod_id,
                "quantity": 1,
                "sales": 100.0,
                "discount": 0.0,
                "profit": 20.0
            }
        ]
    }
    resp = client.post("/api/v1/orders", json=illegal_payload, headers=superstore_headers)
    assert resp.status_code == 400
    assert "Cross-Tenant Violation" in resp.json()["detail"]
    assert "Store ID" in resp.json()["detail"]


def test_cross_tenant_order_creation_with_foreign_product_rejected(client: TestClient):
    """
    TEST-ISO-06: Proves Superstore cannot create an order containing Nike's product.
    """
    # 1. Fetch Nike's product SKU
    nike_token = get_token(client, username="nike.admin")
    nike_headers = {"Authorization": f"Bearer {nike_token}", "X-Company-ID": "2"}
    nike_prod_id = client.get("/api/v1/products?limit=1", headers=nike_headers).json()["items"][0]["product_id"]

    # 2. Fetch Superstore's customer
    superstore_token = get_token(client, username="superstore.admin")
    superstore_headers = {"Authorization": f"Bearer {superstore_token}", "X-Company-ID": "1"}
    superstore_cust_id = client.get("/api/v1/customers?limit=1", headers=superstore_headers).json()["items"][0]["customer_id"]

    # 3. Attempt to create order in Superstore with Nike's product
    illegal_payload = {
        "order_id": "ILLEGAL-ORD-003",
        "order_date": str(date.today()),
        "customer_id": superstore_cust_id,
        "lines": [
            {
                "product_id": nike_prod_id,  # Foreign Product SKU!
                "quantity": 1,
                "sales": 100.0,
                "discount": 0.0,
                "profit": 20.0
            }
        ]
    }
    resp = client.post("/api/v1/orders", json=illegal_payload, headers=superstore_headers)
    assert resp.status_code == 400
    assert "Cross-Tenant Violation" in resp.json()["detail"]
    assert "Product" in resp.json()["detail"]


def test_puma_cannot_access_superstore_records(client: TestClient):
    """
    TEST-ISO-07: Proves Puma Admin (Company 3) cannot access Superstore orders.
    """
    superstore_token = get_token(client, username="superstore.admin")
    superstore_headers = {"Authorization": f"Bearer {superstore_token}", "X-Company-ID": "1"}
    superstore_order_id = client.get("/api/v1/orders?limit=1", headers=superstore_headers).json()["items"][0]["order_id"]

    puma_token = get_token(client, username="puma.admin")
    puma_headers = {"Authorization": f"Bearer {puma_token}", "X-Company-ID": "3"}

    leak_resp = client.get(f"/api/v1/orders/{superstore_order_id}", headers=puma_headers)
    assert leak_resp.status_code == 404
    assert "not found in this company" in leak_resp.json()["detail"]


def test_company_admin_cannot_provision_company(client: TestClient):
    """
    TEST-ISO-08: Proves Company Admin cannot access Platform Admin endpoint POST /api/v1/companies.
    """
    superstore_token = get_token(client, username="superstore.admin")
    superstore_headers = {"Authorization": f"Bearer {superstore_token}", "X-Company-ID": "1"}

    resp = client.post("/api/v1/companies", json={"company_name": "Rogue Corp"}, headers=superstore_headers)
    assert resp.status_code == 403
    assert "Platform Administrator privileges required" in resp.json()["detail"]
