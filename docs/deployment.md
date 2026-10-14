# Deployment Architecture & Production Readiness Guide

## 1. Production Topology

```mermaid
flowchart LR
    ClientBrowser["Client Browser (HTTPS)"]
    
    subgraph ReverseProxy["Edge / Reverse Proxy (Nginx / IIS / Cloudflare)"]
        SSLTermination["TLS 1.3 Termination"]
        StaticRouter["Static Router (/ -> React SPA)"]
        APIRouter["API Proxy (/api/v1 -> Backend)"]
    end

    subgraph AppHost["Application Host Server"]
        UvicornWorkers["FastAPI Application (Uvicorn / Gunicorn Workers)"]
    end

    subgraph DBHost["Database Host"]
        SQLCluster[("Microsoft SQL Server\nSalesManagementDB")]
    end

    ClientBrowser --> SSLTermination
    SSLTermination --> StaticRouter
    SSLTermination --> APIRouter
    APIRouter --> UvicornWorkers
    UvicornWorkers -->|ODBC Driver 17 (Encrypted)| SQLCluster
```

---

## 2. Environment Configuration & Security Hardening

1. **Secret Storage**:
   - `SECRET_KEY` must be generated randomly (`openssl rand -hex 32`) and supplied via secure container/server environment variables.
   - Never commit `.env` or secrets to source control.
2. **CORS Restrictions**:
   - `CORS_ORIGINS` in production must explicitly name the verified production frontend domains (e.g. `https://sales.company.com`).
3. **Database Credentials**:
   - In production Windows environments, use a dedicated Windows service account with Managed Service Identity (gMSA) or minimum-privilege SQL authentication.
4. **HTTPS Enforcement**:
   - In production, set `SESSION_COOKIE_SECURE=true` and enforce HSTS headers at the reverse proxy.

---

## 3. Migration & Rollout Strategy

1. **Migration Verification**:
   - Run SQL migration scripts in transaction blocks (`BEGIN TRANSACTION ... COMMIT TRANSACTION`).
   - Test migrations against staging replicas before applying to production.
2. **Zero-Downtime Principles**:
   - Make additive schema changes first (new tables/columns).
   - Deploy backend code that supports both old and new schema.
   - Decommission obsolete columns in subsequent maintenance windows.

---

## 4. Health Checks & Monitoring

- **Endpoint**: `GET /api/v1/health`
- **Behavior**: Verifies connectivity to Microsoft SQL Server (`SELECT 1`).
- **Safe Output**: Returns status `{"status": "healthy", "database": "connected"}` without exposing internal server paths, database names, or version numbers.
