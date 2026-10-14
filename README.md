# SIMS — Sales Intelligence and Management System

An enterprise-grade, multi-tenant SaaS business solution built for multi-store retail, inventory orchestration, flexible data ingestion, and sales intelligence.

[![Backend Tests](https://img.shields.io/badge/pytest-50%20passed%20(100%25)-brightgreen.svg)]()
[![TypeScript](https://img.shields.io/badge/TypeScript-0%20errors-blue.svg)]()
[![Frontend Build](https://img.shields.io/badge/Vite%20Build-Passing-success.svg)]()
[![Database](https://img.shields.io/badge/MongoDB-Multi--Tenant-green.svg)]()
[![Architecture](https://img.shields.io/badge/Architecture-React%20%2B%20FastAPI%20%2B%20MongoDB-purple.svg)]()

---

## 1. Executive Summary & Architecture

SIMS enables independent companies (tenants) to manage their multi-store businesses, product catalogs, inventories, customer directories, order pipelines, and analytical reporting on a single centralized software platform with strict, backend-enforced tenant isolation.

### Key Capabilities

- **Multi-Tenant Hierarchy**: `SIMS Platform` ➔ `Company (Tenant)` ➔ `Stores / Locations` ➔ `Users & Business Data`.
- **Consolidated vs Store-Level Visibility**: View aggregated metrics across all authorized stores or filter instantly down to an individual branch.
- **Multi-Store Inventory Management**: Real-time stock levels, low-stock reorder alerts, out-of-stock monitoring, stock adjustments, supplier receipts, and traceable inter-store transfers with bilateral movement logs and CSV exports.
- **Flexible Data Ingestion (Dual Path)**:
  - **Path A (Raw Dataset Ingestion)**: Ingests arbitrary CSV files and preserves all source columns without data loss, enabling instant querying and full-text inspection.
  - **Path B (Structured Business Import)**: Interactive column-mapping wizard with schema detection, type validation, store assignment, and duplicate prevention.
- **External Connectors & Integrations**: Integration framework supporting POS REST APIs, E-Commerce webhooks, and mock store connectors with cursor checkpoints, incremental synchronization, and audit history.
- **Enterprise Security**: Enforced multi-tenant isolation dependencies, cryptographic password hashing (PBKDF2-HMAC-SHA256, 100k rounds), JWT HS256 tokens, and RBAC permission checks on every route.

```
┌────────────────────────────────────────────────────────┐
│                   React 18 Frontend                    │
│   (Dashboard, Orders, Inventory, Products, Customers,  │
│    Flexible CSV Import, Integrations, Multi-Store UI)  │
└───────────────────────────┬────────────────────────────┘
                            │ REST / JSON (JWT Bearer + X-Company-ID)
┌───────────────────────────▼────────────────────────────┐
│                  FastAPI Backend v1                    │
│   (Dependencies: Auth, TenantContext, RBAC Matrix)     │
│  Services: Auth, Inventory, Import, Analytics, Connect │
│   Repositories: PyMongo Aggregations & Query Filters   │
└───────────────────────────┬────────────────────────────┘
                            │ PyMongo Driver (or transparent mongomock fallback)
┌───────────────────────────▼────────────────────────────┐
│                    MongoDB Database                    │
│    (Collections: companies, stores, users, memberships,│
│     products, inventory, inventory_movements, orders,  │
│     customers, raw_datasets, integrations, sync_logs)  │
└────────────────────────────────────────────────────────┘
```

---

## 2. Configured Demo Accounts

In compliance with the specification, exactly **three demo companies** are seeded, each with exactly **one Admin** and **one Employee** account, plus a separate **Platform Super Administrator**:

| Company | Role | Username | Email | Visibility & Permissions |
| :--- | :--- | :--- | :--- | :--- |
| **Platform** | Super Administrator | `superadmin` | `admin@platform.sims` | System-wide cross-tenant administration & tenant management |
| **Superstore** | Company Admin | `superstore.admin` | `admin@superstore.sims.local` | Consolidated visibility across Manhattan, Chicago, and LA stores |
| **Superstore** | Employee | `superstore.employee` | `employee@superstore.sims.local` | Store 1 (Manhattan Flagship) store-restricted operations |
| **Nike** | Company Admin | `nike.admin` | `admin@nike.sims.local` | Consolidated visibility across SoHo NYC and Chicago stores |
| **Nike** | Employee | `nike.employee` | `employee@nike.sims.local` | Store 4 (SoHo NYC) store-restricted operations |
| **Puma** | Company Admin | `puma.admin` | `admin@puma.sims.local` | Consolidated visibility across Fifth Ave NYC and Santana Row stores |
| **Puma** | Employee | `puma.employee` | `employee@puma.sims.local` | Store 6 (Fifth Ave NYC) store-restricted operations |

### Demo Password
The shared password for all demo accounts is configured via the `DEMO_PASSWORD` environment variable (default: `Demo12345!`).

---

## 3. Quick Start & Local Setup

### Prerequisites
- **Python 3.10+** (tested on Python 3.13)
- **Node.js 18+** (tested on Node v24)
- **MongoDB** (running locally on port 27017, or set `USE_MOCK_MONGO=true` for zero-install instant execution)

### 1. Backend Setup & Seed
```powershell
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run deterministic demo seed
python -m app.db.seed

# Start FastAPI development server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/v1/health`

### 2. Frontend Setup
```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
- Access application: `http://localhost:5173`

---

## 4. Automated Testing & Verification

The test suite validates backend security, tenant isolation, role authorization, multi-store inventory workflows, and import pipelines:

```powershell
# Run the complete test suite
pytest backend/tests
```

### Verified Test Results
```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-8.3.3, pluggy-1.6.0
rootdir: C:\Users\Sufian\Desktop\Sales management system\backend
configfile: pytest.ini

backend\tests\test_auth_api.py ........                                  [ 16%]
backend\tests\test_business_apis.py .....                                [ 26%]
backend\tests\test_health.py ..                                          [ 30%]
backend\tests\test_import_api.py ......                                  [ 42%]
backend\tests\test_integrations_api.py ...                               [ 48%]
backend\tests\test_inventory_api.py ..........                           [ 68%]
backend\tests\test_security.py ...                                       [ 74%]
backend\tests\test_tenant_dependency.py .....                            [ 84%]
backend\tests\test_tenant_isolation.py ........                          [100%]

============================= 50 passed in 19.93s =============================
```

---

## 5. Security & Multi-Tenant Data Isolation

SIMS enforces multi-tenant boundary checks in the backend application layer before queries hit MongoDB:

1. **JWT Signature & Claims**: JWT tokens encode the user ID and tenant roles.
2. **`TenantContext` Dependency**: Extracts tenant context and validates that the requested company ID belongs to the user's active membership.
3. **Cross-Tenant Validation**: Prevents any tenant from accessing, modifying, or creating orders/inventory referencing foreign store IDs or customer IDs (verified in `test_tenant_isolation.py`).
4. **CSV Injection Protection**: Exported CSV files sanitize fields starting with `=`, `+`, `-`, or `@` to eliminate formula execution vulnerabilities in Excel.
5. **No Production Secrets in Git**: Managed via `.env` configuration files.
