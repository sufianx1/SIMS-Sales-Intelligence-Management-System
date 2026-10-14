# Architecture Decision Records (ADR)

## ADR 001: Full-Stack Rebuild (FastAPI + React) vs. Monolithic Streamlit

### Status
Accepted

### Context
The original internship project was prototyped as a single-node Streamlit application with Python script-based re-execution. As the business requirements expanded to include multi-tenant isolation, role-based access control, store hierarchy, and enterprise-grade UI/UX, the Streamlit model proved inadequate for fine-grained authorization, client-side caching, and professional user workflows.

### Decision
Reconstruct the application as an enterprise decoupled full-stack architecture:
- **Backend**: FastAPI with Python for high throughput, asynchronous execution, Pydantic validation, and clean layered design.
- **Frontend**: React 19 + TypeScript + Vite + Bootstrap 5 + React Router + Plotly.js for responsive state management, client routing, and robust component architecture.

---

## ADR 002: Multi-Tenancy Strategy (Shared Database with Tenant ID Scoping)

### Status
Accepted

### Context
We evaluated three tenancy models:
1. Database-per-tenant
2. Schema-per-tenant
3. Shared Database with Tenant ID Scoping and Composite Foreign Keys

### Decision
Adopt **Shared Database with Tenant ID Scoping**:
- `CompanyID` is added to all tenant-owned entities (`Customers`, `Products`, `Orders`, `Stores`, `UserCompanies`).
- Stores enforce composite integrity: `Stores (StoreID, CompanyID)`.
- Orders enforce composite foreign keys: `FOREIGN KEY (StoreID, CompanyID) REFERENCES Stores (StoreID, CompanyID)`.
- Rationale: High scalability, cost-effective resource utilization on SQL Server, simple global analytics across authorized tenants, and bulletproof database-level foreign key constraints.

---

## ADR 003: Direct Parameterized `pyodbc` vs. Heavy Object-Relational Mappers (ORM)

### Status
Accepted

### Context
SQL Server features complex aggregate queries, CTEs, and specific date/financial precision rules. Heavy ORMs (such as SQLAlchemy or Django ORM) frequently generate sub-optimal SQL for multi-dimensional aggregations and obscure query execution plans.

### Decision
Use **Direct Parameterized `pyodbc` within a clean Repository Pattern**:
- Every query is 100% parameterized with positional placeholders (`?`), guaranteeing complete immunity to SQL injection.
- Repositories return clean domain dictionaries and Pandas DataFrames.
- Developers maintain explicit control over SQL queries, indexes, and execution plans.

---

## ADR 004: Two-Tier Tenant Resolution & Access Control

### Status
Accepted

### Context
Users may have memberships across multiple companies (e.g., consultants, platform administrators, or executives managing multiple brands like Superstore, Nike, and Puma).

### Decision
1. User logs in with global identity (`Email`, `PasswordHash`).
2. Authentication returns all authorized company memberships and roles.
3. Client selects an active tenant, transmitted via `X-Company-ID` header.
4. Backend middleware/dependency validates that the authenticated user is an active member of the specified `CompanyID` on every single request before handing execution to the service layer.

---

## ADR 005: Database Preservation & Non-Destructive Migration Policy

### Status
Accepted

### Context
The database `SalesManagementDB` already exists on `localhost` with existing customer, order, company, and user records.

### Decision
Follow a strict non-destructive policy:
- Never drop or recreate `SalesManagementDB`.
- Write idempotent, version-controlled migration scripts.
- Validate and accommodate existing data structures while enhancing indexes, constraints, and audit tables.
