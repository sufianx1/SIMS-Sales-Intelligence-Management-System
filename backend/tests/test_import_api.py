"""
backend/tests/test_import_api.py
--------------------------------
Integration tests for CSV validation, Path A Raw datasets, and Path B structured ETL imports,
including cross-tenant store isolation checks.
"""

import io
import uuid
import json
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


def test_import_validate_valid_csv(client: TestClient):
    headers = get_auth_headers(client)
    csv_data = (
        "Order ID,Order Date,Ship Date,Ship Mode,Customer ID,Customer Name,Segment,Country,City,State,Postal Code,Region,Product ID,Category,Sub-Category,Product Name,Sales,Quantity,Discount,Profit\n"
        "TEST-ORD-01,2026-01-15,2026-01-18,Standard Class,TC-01,Alice Smith,Consumer,United States,Seattle,Washington,98101,West,TP-01,Technology,Phones,Super Phone,299.99,1,0.0,50.00\n"
    ).encode("utf-8")

    files = {"file": ("test.csv", io.BytesIO(csv_data), "text/csv")}
    resp = client.post("/api/v1/imports/validate", files=files, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["total_rows"] == 1
    assert len(data["sample_preview"]) == 1


def test_import_validate_invalid_csv_missing_columns(client: TestClient):
    headers = get_auth_headers(client)
    csv_data = "Order ID,Product Name\nORD-1,Widget\n".encode("utf-8")

    files = {"file": ("bad.csv", io.BytesIO(csv_data), "text/csv")}
    resp = client.post("/api/v1/imports/validate", files=files, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is False
    assert len(data["missing_columns"]) > 0


def test_import_execute_transactional_success(client: TestClient):
    headers = get_auth_headers(client)
    uid = uuid.uuid4().hex[:6]
    csv_data = (
        "Order ID,Order Date,Ship Date,Ship Mode,Customer ID,Customer Name,Segment,Country,City,State,Postal Code,Region,Product ID,Category,Sub-Category,Product Name,Sales,Quantity,Discount,Profit\n"
        f"IMP-ORD-{uid},2026-02-10,2026-02-12,First Class,IMP-C-{uid},Bob Jones,Corporate,United States,Denver,Colorado,80202,West,IMP-P-{uid},Office Supplies,Binders,Heavy Binder,45.50,2,0.0,15.20\n"
    ).encode("utf-8")

    # Store 2 belongs to Superstore (Company 1)
    files = {"file": ("import.csv", io.BytesIO(csv_data), "text/csv")}
    resp = client.post("/api/v1/imports/execute", files=files, data={"store_id": 2}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["orders_upserted"] >= 1
    assert data["order_details_inserted"] >= 1


def test_import_execute_foreign_store_rejected(client: TestClient):
    headers = get_auth_headers(client)
    uid = uuid.uuid4().hex[:6]
    csv_data = (
        "Order ID,Order Date,Ship Date,Ship Mode,Customer ID,Customer Name,Segment,Country,City,State,Postal Code,Region,Product ID,Category,Sub-Category,Product Name,Sales,Quantity,Discount,Profit\n"
        f"IMP-BAD-{uid},2026-02-10,2026-02-12,First Class,IMP-C-{uid},Bob Jones,Corporate,United States,Denver,Colorado,80202,West,IMP-P-{uid},Office Supplies,Binders,Heavy Binder,45.50,2,0.0,15.20\n"
    ).encode("utf-8")

    # Store 99 does NOT belong to Superstore (Company 1)
    files = {"file": ("import.csv", io.BytesIO(csv_data), "text/csv")}
    resp = client.post("/api/v1/imports/execute", files=files, data={"store_id": 99}, headers=headers)
    assert resp.status_code == 400
    assert "does not belong to active company" in resp.json()["detail"]


def test_path_a_raw_dataset_import_and_query(client: TestClient):
    headers = get_auth_headers(client)
    raw_csv = "Vendor,RawCode,CustomField,Score\nAcmeSupply,V-999,SpecialVal,98.5\nBetaDist,V-888,OtherVal,87.2\n".encode("utf-8")
    files = {"file": ("raw_vendors.csv", io.BytesIO(raw_csv), "text/csv")}

    # 1. Upload raw dataset
    raw_resp = client.post("/api/v1/imports/raw", files=files, headers=headers)
    assert raw_resp.status_code == 201
    raw_data = raw_resp.json()
    assert raw_data["total_rows"] == 2
    assert "Vendor" in raw_data["columns"]
    import_id = raw_data["import_id"]

    # 2. Query raw dataset detail
    detail_resp = client.get(f"/api/v1/imports/raw/{import_id}?search=Acme", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["rows"]) == 1
    assert detail["rows"][0]["Vendor"] == "AcmeSupply"


def test_path_b_structured_product_import(client: TestClient):
    headers = get_auth_headers(client)
    prod_csv = "SKU_Code,Item_Title,Item_Category,Unit_Cost,Selling_Price\nIMP-PROD-X1,Wireless Ergonomic Mouse,Electronics,22.50,49.99\n".encode("utf-8")
    files = {"file": ("products.csv", io.BytesIO(prod_csv), "text/csv")}
    mapping = {
        "product_id": "SKU_Code",
        "product_name": "Item_Title",
        "category": "Item_Category",
        "unit_cost": "Unit_Cost",
        "unit_price": "Selling_Price"
    }

    resp = client.post(
        "/api/v1/imports/structured",
        files=files,
        data={
            "target_entity": "products",
            "column_mapping_json": json.dumps(mapping)
        },
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["target_entity"] == "products"
    assert data["records_created"] + data["records_updated"] >= 1


def test_import_file_size_limit_exceeded(client: TestClient, monkeypatch):
    headers = get_auth_headers(client)
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 50)

    oversized_csv = ("A" * 100).encode("utf-8")
    files = {"file": ("large.csv", io.BytesIO(oversized_csv), "text/csv")}

    resp = client.post("/api/v1/imports/preview", files=files, headers=headers)
    assert resp.status_code == 413
    assert "File exceeds maximum allowed size" in resp.json()["detail"]

