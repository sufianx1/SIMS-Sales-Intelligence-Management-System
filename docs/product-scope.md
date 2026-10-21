# Product Scope: SIMS (Sales Intelligence and Management System)

## 1. Executive Summary & Purpose

**SIMS (Sales Intelligence and Management System)** is an enterprise multi-tenant SaaS application designed to provide multi-store retail organizations with consolidated operations, real-time inventory management, flexible dual-path data ingestion, and explainable sales analytics.

---

## 2. Target Users & Personas

1. **Company Executive / Brand Administrator**:
   - Needs consolidated visibility across all regional and flagship store branches.
   - Requires real-time KPI tracking (Revenue, Profit, Margin, AOV, Active SKUs).
   - Manages store locations, user permissions, and external integrations.
2. **Store Manager / Branch Employee**:
   - Strictly restricted to their assigned store branch.
   - Manages local stock on hand, logs supplier receipts, and conducts inter-store stock transfers.
   - Creates and tracks retail orders and customers within their location.
3. **Data Analyst / Operations Specialist**:
   - Ingests raw tabular transaction logs without schema restriction (Path A).
   - Maps, validates, and imports structured business entities into production catalogs (Path B).
   - Analyzes explainable business insights to detect low margins, stock shortages, and revenue risks.
4. **Platform Administrator**:
   - Oversees multi-tenant onboarding, tenant status, and platform health across independent companies.

---

## 3. Demo Environment Scope

The demonstration environment is configured with **three distinct commercial tenants**, each seeded with synthetic data:

| Company | Code | Assigned Stores | Demo Accounts |
| :--- | :--- | :--- | :--- |
| **Superstore** | `SUP` | Store 1 (Manhattan Flagship), Store 2 (Chicago Loop), Store 3 (LA Arts District) | Admin: `superstore.admin`<br>Employee: `superstore.employee` (Store 1) |
| **Nike** | `NKE` | Store 4 (Nike SoHo NYC), Store 5 (Nike Michigan Ave Chicago) | Admin: `nike.admin`<br>Employee: `nike.employee` (Store 4) |
| **Puma** | `PMA` | Store 6 (Puma Fifth Ave NYC), Store 7 (Puma Santana Row San Jose) | Admin: `puma.admin`<br>Employee: `puma.employee` (Store 6) |
| **Platform** | `PLT` | Cross-tenant administration | Superadmin: `superadmin` |

*Default shared demo password: `Demo12345!` (configurable via `DEMO_PASSWORD` environment variable).*

---

## 4. In-Scope Demo Capabilities

- **Multi-Tenant Scoping**: Header-based `X-Company-ID` validation with membership verification and cross-tenant reference protection.
- **Multi-Store Inventory Orchestration**: Real-time stock levels, low-stock reorder alerts, supplier receipts, and atomic inter-store transfers with movement audit history.
- **Dual-Path CSV Data Ingestion**:
  - *Path A (Raw Ingestion)*: Uploads arbitrary CSVs, preserves all columns verbatim, and allows ad-hoc search.
  - *Path B (Structured Import)*: Interactive field mapping, validation, duplicate prevention, and transactional entity creation.
- **Analytics & Explainable Insights**: Revenue, Profit, Margin, Order Count, Average Order Value (AOV), monthly trend curves, category/regional breakdowns, and rule-based operational insights with explicit rationale.
- **Reference External Connectors**: POS and E-Commerce mock connectors with cursor checkpoint tracking and sync logs.
- **Pristine Reset**: Automated demo reset utility via `python scripts/reset_demo.py`.

---

## 5. Explicit Out-of-Scope Exclusions (Future Commercial Phase)

The following capabilities are deliberately excluded from the public demonstration scope:
- Live external POS hardware and commercial third-party cloud integrations (Shopify, Square).
- Self-service automated tenant registration and payment gateway billing.
- Machine learning forecasting, predictive chatbots, or generative AI summaries.
- Production multi-region database sharding.
