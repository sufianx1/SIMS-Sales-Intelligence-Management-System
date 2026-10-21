# System Architecture & Verification Audit: SIMS

## 1. Executive Summary

This document records the architectural audit and empirical verification of the **Sales Intelligence and Management System (SIMS)**. All findings and statuses are based on direct source code inspection and test execution.

---

## 2. Technical Stack Verification

| Tier | Documented Specification | Actual Verified Codebase | Status |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | React + TypeScript + Vite | React 18.3.1, TypeScript 5.6.3, Vite 6.4.4 | VERIFIED |
| **Styling & Charts** | Bootstrap 5 + Plotly.js | Bootstrap 5.3.3, Plotly.js | VERIFIED |
| **Backend Framework** | Python FastAPI | FastAPI 0.115.0, Python 3.13.5, Pydantic v2 | VERIFIED |
| **Database Engine** | MongoDB | PyMongo 4.8.0, mongomock 4.3.0 | VERIFIED |
| **Development DB** | MongoDB Atlas `sims_dev` | Live connection verified via Compass & Python | VERIFIED |
| **Test Database** | Isolated `sims_test_db` | In-memory `mongomock` in `conftest.py` | VERIFIED |

---

## 3. Confirmed Defects & Resolutions

| Defect ID | Severity | Description | Root Cause | Status | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DEF-001** | P0 | Missing `pymongo` in requirements | `pyodbc` listed instead of `pymongo` | RESOLVED | `requirements.txt` updated; startup clean |
| **DEF-002** | P0 | RBAC uppercase permission mismatch | `CREATE_ORDER` vs seeded `create_order` | RESOLVED | Normalized to lowercase across all routes |
| **DEF-003** | P1 | Column mapping form field mismatch | Frontend sent `column_mappings`, backend wanted `column_mapping_json` | RESOLVED | Aligned on `column_mapping_json` with fallback |
| **DEF-004** | P1 | Unauthenticated `/imports/validate` | Route lacked authentication dependency | RESOLVED | Added `require_permission("import_data")` |
| **DEF-005** | P2 | Obsolete SQL Server architecture docs | Docs described SQL Server and pyodbc | RESOLVED | Rewrote `docs/architecture.md` & `database-design.md` |
| **DEF-006** | P1 | Seed line-item sales discrepancy | Pre-discount sales used in order lines | RESOLVED | Updated `SUP-ORD-2026-002` & `NKE-ORD-2026-002` |
| **DEF-007** | P1 | Uncontrolled file upload memory risk | No file size cap on CSV imports | RESOLVED | Enforced 15MB limit with HTTP 413 |
| **DEF-008** | P2 | Missing Average Order Value KPI | Not exposed on executive dashboard | RESOLVED | Added AOV to schemas, repo, and UI |
| **DEF-009** | P2 | Lack of explainable insights | No dedicated detection explanation | RESOLVED | Implemented `/analytics/insights` and UI |

---

## 4. Verification Evidence & Test Execution

### Backend Automated Test Suite
- **Command**: `python -m pytest backend/tests -v`
- **Result**: **64 passed in 14.50s** (100% pass rate).
- **Isolation**: Verified that `sims_dev` on Atlas is untouched by test executions.

### Frontend Production Build
- **Command**: `npm run build` (from `frontend/`)
- **Result**: **Built successfully in 30.81s** with 0 TypeScript errors.

### Database Persistence & Demo Reset
- **Command**: `python scripts/reset_demo.py`
- **Result**: Verified clean seeding of 3 companies, 7 stores, 7 users, 15 products, 36 inventory records, 6 orders, 9 customers, 3 integrations in `sims_dev` on MongoDB Atlas with credentials safely masked.
