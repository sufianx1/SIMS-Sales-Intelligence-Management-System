# Deployment Architecture & Production Readiness Guide

## 1. Production Topology

```mermaid
flowchart LR
    ClientBrowser["Client Browser (HTTPS)"]
    
    subgraph ReverseProxy["Edge / Reverse Proxy (Nginx / Cloudflare)"]
        SSLTermination["TLS 1.3 Termination"]
        StaticRouter["Static Router (/ -> React SPA)"]
        APIRouter["API Proxy (/api/v1 -> Backend)"]
    end

    subgraph AppHost["Application Host Server"]
        UvicornWorkers["FastAPI Application (Uvicorn Workers)"]
    end

    subgraph DBHost["Database Host"]
        MongoCluster[("MongoDB Atlas Cluster\nsims_dev / Production DB")]
    end

    ClientBrowser --> SSLTermination
    SSLTermination --> StaticRouter
    SSLTermination --> APIRouter
    APIRouter --> UvicornWorkers
    UvicornWorkers -->|PyMongo Driver (TLS Encrypted)| MongoCluster
```

---

## 2. Environment Configuration & Security Hardening

1. **Secret Storage**:
   - `SECRET_KEY` must be generated cryptographically (`openssl rand -hex 32`) with at least 32 characters and supplied via environment variables.
   - The application enforces fast-fail startup: in `production` or `staging`, default insecure secret keys are strictly rejected.
   - Never commit `.env` or secrets to version control.
2. **CORS Restrictions**:
   - `CORS_ORIGINS` in production must explicitly name the verified production frontend domains (e.g. `https://sims.company.com`).
3. **Database Credentials & Masking**:
   - Store MongoDB connection strings in environment variables (`MONGODB_URI`).
   - The database layer automatically masks credentials in all application log entries using regular expression sanitization (`re.sub`).
4. **HTTPS Enforcement**:
   - Enforce TLS 1.3 and HSTS headers at the edge reverse proxy.
   - Set secure token cookies where cookie-based authentication is enabled.

---

## 3. Database Safety, Backup & Recovery

1. **Automated Backups (MongoDB Atlas)**:
   - For cloud-hosted MongoDB Atlas, enable continuous cloud backups with point-in-time recovery (PITR) and daily retention snapshots.
2. **Self-Hosted Backup Procedures**:
   - **Backup**:
     ```bash
     mongodump --uri="$MONGODB_URI" --db="$MONGODB_DB_NAME" --archive="/backups/sims_$(date +%Y%m%d).archive" --gzip
     ```
   - **Restore**:
     ```bash
     mongorestore --uri="$MONGODB_URI" --db="$MONGODB_DB_NAME" --archive="/backups/sims_20261021.archive" --gzip --drop
     ```
3. **Demo Reset Safety**:
   - `scripts/reset_demo.py` is guarded: it automatically aborts if `ENVIRONMENT` is set to `production` or `staging`.
   - Automated tests run exclusively against in-memory `mongomock` (`sims_test_db`), guaranteeing zero contamination of development or production databases.

---

## 4. Health & Readiness Probes

- **Liveness Probe**: `GET /api/v1/health`
  - Verifies operational liveness and reports database reachability (`status: healthy`, `database: connected`).
  - Never exposes internal connection strings, database credentials, or server filepaths.
- **Readiness Probe**: `GET /api/v1/ready`
  - Executes a `ping` command against MongoDB.
  - Returns HTTP `200 OK` when ready to receive production traffic; returns HTTP `503 Service Unavailable` if database connectivity is degraded.
