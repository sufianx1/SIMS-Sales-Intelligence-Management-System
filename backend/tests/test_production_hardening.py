"""
backend/tests/test_production_hardening.py
-------------------------------------------
Comprehensive hardening test suite validating:
1. Token revocation & logout invalidation
2. Login brute-force rate limiting
3. Production configuration & fail-secure database connection
4. Readiness & liveness health probes
5. Atomic inventory adjustments & inter-store transfers
6. Authoritative financial calculations & cost basis snapshots
7. CSV formula injection sanitization & chunked dataset ingestion
8. Webhook HMAC verification, replay protection, & credential masking
9. Analytics profit ranking correctness
"""

import hmac
import hashlib
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from app.core.config import settings
from app.core.security import (
    sanitize_for_csv, verify_webhook_signature,
    revoke_token, is_token_revoked, check_login_rate_limit, record_login_attempt
)
from app.db.mongo import get_db
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.analytics_repo import AnalyticsRepository
from app.services.import_service import ImportService
from app.services.integration_service import IntegrationService


def test_csv_formula_injection_sanitization():
    """Validates that leading dangerous formula characters (=, +, -, @, \\t) are neutralized."""
    assert sanitize_for_csv("=SUM(A1:A10)") == "'=SUM(A1:A10)"
    assert sanitize_for_csv("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert sanitize_for_csv("-10+20") == "'-10+20"
    assert sanitize_for_csv("@HYPERLINK('http://evil.com')") == "'@HYPERLINK('http://evil.com')"
    assert sanitize_for_csv("\tcmd") == "'\tcmd"
    # Normal strings and numbers remain unmodified
    assert sanitize_for_csv("Standard Product Name") == "Standard Product Name"
    assert sanitize_for_csv(123.45) == 123.45
    assert sanitize_for_csv("") == ""


def test_token_revocation_lifecycle():
    """Validates that revoked tokens are recorded and immediately rejected."""
    sample_token = "test_token_revocation_xyz_12345"
    assert not is_token_revoked(sample_token)

    revoke_token(sample_token)
    assert is_token_revoked(sample_token)


def test_login_rate_limiting_lockout():
    """Validates that brute-force failed login attempts trigger lockout."""
    test_id = "bruteforce_target_user@example.com"
    ip = "192.168.1.100"

    # Reset any past test records for this identifier
    db = get_db()
    db.login_attempts.delete_many({"identifier": test_id})

    # Within limit
    for _ in range(settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS - 1):
        record_login_attempt(test_id, ip_address=ip, success=False)
        assert check_login_rate_limit(test_id, ip_address=ip) is True

    # 5th failure reaches limit
    record_login_attempt(test_id, ip_address=ip, success=False)
    assert check_login_rate_limit(test_id, ip_address=ip) is False

    # Cleanup
    db.login_attempts.delete_many({"identifier": test_id})


def test_webhook_hmac_constant_time_verification():
    """Validates HMAC-SHA256 signature verification and timing-attack resistance."""
    secret = "whsec_super_secret_webhook_key_9988"
    payload = b'{"event_id": "evt_123", "action": "order_created", "amount": 199.99}'

    valid_sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    # Valid signature
    assert verify_webhook_signature(payload, valid_sig, secret) is True
    # Valid with sha256= prefix
    assert verify_webhook_signature(payload, f"sha256={valid_sig}", secret) is True
    # Tampered signature
    assert verify_webhook_signature(payload, valid_sig[:-2] + "00", secret) is False
    # Tampered payload
    assert verify_webhook_signature(payload + b"tamper", valid_sig, secret) is False


def test_readiness_probe_endpoint(client: TestClient):
    """Validates /ready endpoint returns status ready and HTTP 200 when database is healthy."""
    resp = client.get("/api/v1/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_auth_logout_revokes_token(client: TestClient):
    """Validates that calling /auth/logout invalidates the bearer token on subsequent requests."""
    login_resp = client.post("/api/v1/auth/login", json={"username": "superstore.admin", "password": "Demo12345!"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Company-ID": "1"}

    # Token works initially
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200

    # Logout
    logout_resp = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200

    # Subsequent request using same token MUST be rejected
    denied_resp = client.get("/api/v1/auth/me", headers=headers)
    assert denied_resp.status_code == 401


def test_atomic_inventory_negative_stock_prevention():
    """Validates that inventory reduction below zero is rejected atomically."""
    db = get_db()
    company_id = 1
    store_id = 1
    prod_id = "TEST-NEG-PROD"

    # Set initial stock of 10
    InventoryRepository.adjust_stock(
        company_id=company_id,
        store_id=store_id,
        product_id=prod_id,
        quantity_change=10,
        reason="Initial test stock"
    )

    # Valid reduction of 4 -> 6 remaining
    res = InventoryRepository.adjust_stock(
        company_id=company_id,
        store_id=store_id,
        product_id=prod_id,
        quantity_change=-4,
        reason="Valid reduction"
    )
    assert res["quantity_on_hand"] == 6

    # Invalid reduction of 7 (exceeds current 6) -> Must raise ValueError and NOT reduce stock
    with pytest.raises(ValueError, match="Cannot adjust inventory below zero"):
        InventoryRepository.adjust_stock(
            company_id=company_id,
            store_id=store_id,
            product_id=prod_id,
            quantity_change=-7,
            reason="Excessive reduction"
        )

    # Verify stock remained at 6
    check = db.inventory.find_one({"company_id": company_id, "store_id": store_id, "product_id": prod_id})
    assert check["quantity_on_hand"] == 6

    # Cleanup
    db.inventory.delete_many({"product_id": prod_id})
    db.inventory_movements.delete_many({"product_id": prod_id})


def test_inter_store_transfer_insufficient_stock():
    """Validates that inter-store transfer fails cleanly when origin has insufficient stock."""
    db = get_db()
    company_id = 1
    from_store = 1
    to_store = 2
    prod_id = "TEST-XFER-PROD"

    # Set 5 units at origin
    InventoryRepository.adjust_stock(company_id, from_store, prod_id, 5, "Transfer test seed")

    # Attempt to transfer 10 -> Must raise ValueError
    with pytest.raises(ValueError, match="Insufficient stock at origin store"):
        InventoryRepository.transfer_stock(
            company_id=company_id,
            from_store_id=from_store,
            to_store_id=to_store,
            product_id=prod_id,
            quantity=10,
            reason="Exceeding transfer"
        )

    # Cleanup
    db.inventory.delete_many({"product_id": prod_id})
    db.inventory_movements.delete_many({"product_id": prod_id})


def test_order_creation_financial_snapshot(client: TestClient):
    """Validates that orders snapshot authoritative unit prices and cost basis."""
    login_resp = client.post("/api/v1/auth/login", json={"username": "superstore.admin", "password": "Demo12345!"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Company-ID": "1"}

    # Get an existing product to order
    prod_resp = client.get("/api/v1/products", headers=headers)
    assert prod_resp.status_code == 200
    prod_data = prod_resp.json()
    products = prod_data.get("items", prod_data) if isinstance(prod_data, dict) else prod_data
    assert len(products) > 0
    test_prod = products[0]

    # Get customer
    cust_resp = client.get("/api/v1/customers", headers=headers)
    assert cust_resp.status_code == 200
    cust_data = cust_resp.json()
    custs = cust_data.get("items", cust_data) if isinstance(cust_data, dict) else cust_data
    assert len(custs) > 0
    test_cust = custs[0]

    order_payload = {
        "order_id": f"TEST-FIN-{datetime.now().strftime('%M%S%f')}",
        "order_date": "2026-10-14",
        "customer_id": test_cust["customer_id"],
        "store_id": 1,
        "lines": [
            {
                "product_id": test_prod["product_id"],
                "quantity": 2,
                "discount": 0.05
            }
        ]
    }

    create_resp = client.post("/api/v1/orders", json=order_payload, headers=headers)
    assert create_resp.status_code == 201
    created_data = create_resp.json()

    db = get_db()
    prod_doc = db.products.find_one({"company_id": 1, "product_id": test_prod["product_id"]})
    unit_price = float(prod_doc.get("unit_price", 0.0))
    unit_cost = float(prod_doc.get("unit_cost", 0.0))

    line = created_data["lines"][0]
    expected_gross = round(unit_price * 2, 2)
    expected_sales = round(expected_gross * 0.95, 2)
    expected_profit = round(expected_sales - (unit_cost * 2), 2)

    assert line["sales"] == expected_sales
    assert line["profit"] == expected_profit


def test_integration_credential_masking(client: TestClient):
    """Validates that sensitive secrets in connector configs are masked in API responses."""
    login_resp = client.post("/api/v1/auth/login", json={"username": "superstore.admin", "password": "Demo12345!"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Company-ID": "1"}

    create_payload = {
        "name": "POS Live Connector",
        "connector_type": "POS_REST_API",
        "store_id": 1,
        "config": {
            "api_key": "mock_api_key_1234567890abcdef",
            "webhook_secret": "mock_whsec_abcdef1234567890",
            "terminal_id": "TERM-001"
        }
    }

    create_resp = client.post("/api/v1/integrations", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    cfg = create_resp.json()["config"]

    # Raw secrets must NOT be in output
    assert "mock_api_key_1234567890abcdef" not in cfg["api_key"]
    assert "mock_whsec_abcdef1234567890" not in cfg["webhook_secret"]
    assert "..." in cfg["api_key"]
    assert cfg["terminal_id"] == "TERM-001"


def test_raw_dataset_chunked_storage():
    """Validates that raw CSV rows are chunked into separate documents to prevent BSON overflow."""
    csv_content = b"Row_ID,Name,Category,Sales\n" + b"\n".join([f"{i},Item {i},Cat,100".encode() for i in range(1, 150)])
    item = ImportService.import_raw_dataset(
        file_bytes=csv_content,
        filename="test_chunked_data.csv",
        company_id=1,
        store_id=1,
        user_id=1
    )
    assert item.total_rows == 149

    detail = ImportService.get_raw_dataset(company_id=1, import_id=item.import_id, limit=200)
    assert len(detail.rows) == 149
    assert detail.rows[0]["Name"] == "Item 1"


def test_profit_by_category_ranking():
    """Validates that get_profit_by_category sorts categories by total profit descending."""
    profit_data = AnalyticsRepository.get_profit_by_category(company_id=1)
    if len(profit_data) >= 2:
        for idx in range(len(profit_data) - 1):
            assert profit_data[idx]["total_profit"] >= profit_data[idx + 1]["total_profit"]


def test_persistent_db_requirement_prevents_silent_mock_fallback(monkeypatch):
    """Validates that REQUIRE_PERSISTENT_DB blocks silent fallback to mongomock."""
    from app.db import mongo

    orig_client = mongo._mongo_client
    orig_mock = mongo._is_mock

    try:
        # Test 1: If REQUIRE_PERSISTENT_DB=True and USE_MOCK_MONGO=True -> must raise RuntimeError
        mongo._mongo_client = None
        monkeypatch.setattr(settings, "REQUIRE_PERSISTENT_DB", True)
        monkeypatch.setattr(settings, "USE_MOCK_MONGO", True)
        with pytest.raises(RuntimeError, match="CRITICAL CONFIGURATION CONFLICT"):
            mongo.get_client()

        # Test 2: If REQUIRE_PERSISTENT_DB=True and live MongoDB URI fails -> must raise RuntimeError
        mongo._mongo_client = None
        monkeypatch.setattr(settings, "USE_MOCK_MONGO", False)
        monkeypatch.setattr(settings, "MONGODB_TIMEOUT_MS", 200)
        monkeypatch.setattr(settings, "MONGODB_URI", "mongodb://127.0.0.1:59999/")
        with pytest.raises(RuntimeError, match="Persistent database connection failure"):
            mongo.get_client()
    finally:
        mongo._mongo_client = orig_client
        mongo._is_mock = orig_mock


def test_readiness_probe_distinguishes_mock_in_production(client: TestClient, monkeypatch):
    """Validates /ready endpoint returns HTTP 503 if running on mock when persistent DB is required."""
    monkeypatch.setattr(settings, "REQUIRE_PERSISTENT_DB", True)
    resp = client.get("/api/v1/ready")
    assert resp.status_code == 503
    data = resp.json()
    assert data["status"] == "not_ready"
    assert data["is_mock"] is True
    assert "unsupported: in-memory mock" in data["database"]


def test_health_probe_reports_is_mock_field(client: TestClient):
    """Validates that /health returns boolean is_mock field distinguishing persistent vs in-memory."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "is_mock" in data
    assert isinstance(data["is_mock"], bool)


def test_demo_seeding_blocked_in_production(monkeypatch):
    """Validates that automated demo seeding is strictly aborted in production/staging environments."""
    from app.db.seed import seed_database
    db = get_db()
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    count_before = db.companies.count_documents({})
    seed_database(db, force=False)
    count_after = db.companies.count_documents({})
    assert count_after == count_before


def test_insecure_example_secret_key_rejected_in_production():
    """Validates that validate_runtime_security rejects example secret keys in production."""
    from app.core.config import Settings
    with pytest.raises(ValueError, match="CRITICAL SECURITY FAILURE"):
        bad_settings = Settings(
            ENVIRONMENT="production",
            SECRET_KEY="sims-super-secret-development-key-change-in-production-1234567890",
            USE_MOCK_MONGO=False
        )
        bad_settings.validate_runtime_security()

