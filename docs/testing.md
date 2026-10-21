# Testing Strategy & Automated Test Specifications

## 1. Testing Philosophy

SIMS treats automated testing as a mandatory quality gate. Every multi-tenant boundary, RBAC permission, financial calculation, and CSV ETL ingestion pathway is verified by automated test suites.

### Test Categories
1. **Security & Authentication Tests** (`test_auth_api.py`, `test_security.py`): Validates PBKDF2 hashing, JWT generation, invalid credentials, token revocation lifecycle, and rate-limiting lockouts.
2. **Tenant Isolation Tests** (`test_tenant_isolation.py`, `test_tenant_dependency.py`): Deliberate adversarial tests proving that Tenant A cannot access, create, or modify records belonging to Tenant B.
3. **Core Business API Tests** (`test_business_apis.py`): Customer, Product, Store, and Order transactional CRUD workflows and explainable insights.
4. **Inventory Management Tests** (`test_inventory_api.py`): Multi-store stock adjustments, receipts, negative inventory prevention, inter-store transfers, low-stock alerts, and CSV export sanitization.
5. **Data Import & ETL Tests** (`test_import_api.py`): CSV header inspection, Path A raw storage, Path B structured imports, column mapping, and 15MB file size limit enforcement.
6. **Production Hardening Tests** (`test_production_hardening.py`): Token revocation, CSV formula injection defense, constant-time HMAC webhook verification, and readiness probe probes.

---

## 2. Test Isolation Guarantee

All automated tests execute in strict isolation from the development and production databases:
- **Test Configuration**: Configured in [`backend/tests/conftest.py`](file:///c:/Users/Sufian/Desktop/Sales%20management%20system/backend/tests/conftest.py).
- **Environment Flags**:
  - `ENVIRONMENT = "testing"`
  - `MONGODB_DB_NAME = "sims_test_db"`
  - `USE_MOCK_MONGO = "true"`
- **Zero Contamination**: Pytest executes exclusively against in-memory `mongomock`. Automated test runs never connect to, modify, or delete records in `sims_dev` on MongoDB Atlas.

---

## 3. Test Execution Commands

### Running Backend Automated Tests
```powershell
# Navigate to backend directory or workspace root
python -m pytest backend/tests -v

# Run with short traceback
python -m pytest backend/tests -q

# Run specific test modules
python -m pytest backend/tests/test_tenant_isolation.py -v
python -m pytest backend/tests/test_import_api.py -v
python -m pytest backend/tests/test_inventory_api.py -v
```

### Running Frontend Production Build & TypeScript Verification
```powershell
cd frontend
npm run build
```
Validates that all TypeScript types, React components, and Vite bundle compilation pass with 0 errors.

---

## 4. Current Test Suite Status

```text
============================= 64 passed in 14.50s =============================
- test_auth_api.py: 8 passed
- test_business_apis.py: 6 passed (including explainable insights)
- test_health.py: 2 passed
- test_import_api.py: 7 passed (including 15MB file limit)
- test_integrations_api.py: 3 passed
- test_inventory_api.py: 10 passed
- test_production_hardening.py: 13 passed
- test_security.py: 3 passed
- test_tenant_dependency.py: 5 passed
- test_tenant_isolation.py: 8 passed
```
