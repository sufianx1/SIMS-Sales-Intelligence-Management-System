# Security Architecture & Tenant Isolation Guidelines

## 1. Multi-Tenant Isolation Strategy

SIMS is engineered with defense-in-depth principles to prevent any possibility of cross-tenant data access, modification, or information leakage.

### 1.1 Never Trust Frontend Tenant Identifiers
The client application transmits the active tenant context via the `X-Company-ID` HTTP request header.
However:
1. **The backend NEVER treats `X-Company-ID` as proof of authorization.**
2. On every protected request, the backend dependency `get_tenant_context()`:
   - Validates and decodes the authenticated JWT bearer token.
   - If the user is a `Platform Admin` (`is_system_admin = True`), access to any valid `company_id` is permitted for platform management.
   - For regular users, the system inspects the `memberships` collection to verify that an active record exists for `(user_id, company_id)`.
   - Extracts the user's specific `role_name`, `store_id`, and granular `permissions` array for that tenant.
   - If the user is not an active member of that company, the request is immediately rejected with HTTP `403 Forbidden`.

### 1.2 Data Access Layer Scoping
Every MongoDB query and aggregation pipeline across the repository layer explicitly enforces tenant scoping:
```python
# CORRECT: Always scoped with company_id filter
db.customers.find_one({"company_id": company_id, "customer_id": customer_id})

# INCORRECT / VULNERABLE: Lacks tenant scoping
# db.customers.find_one({"customer_id": customer_id})
```

### 1.3 Cross-Tenant Reference Validation
When business objects are created or modified, the backend validates that all referenced foreign entities belong to the active company:
- **Order Creation**: Validates that `customer_id`, `store_id`, and every `lines[].product_id` exist in the database with matching `company_id`. Foreign entity references are rejected with HTTP `400 Bad Request`.
- **Inventory Transfers**: Validates that both origin and destination stores belong to `company_id`.

---

## 2. Authentication & Credential Security

1. **Password Hashing**:
   - Passwords are encrypted using PBKDF2-HMAC-SHA256 with 100,000 rounds and a random 32-byte salt.
   - Passwords are never stored in plaintext and never logged.
2. **Timing Attack Defense**:
   - Password verification and HMAC webhook signatures use `secrets.compare_digest()` for constant-time cryptographic comparison, eliminating timing analysis vulnerabilities.
3. **Token Management & Blacklisting**:
   - HS256 JWT tokens include standard claims (`sub`, `exp`, `iat`) and a unique token ID (`jti`).
   - Logging out records the token in the `revoked_tokens` collection with a MongoDB TTL index that automatically purges expired tokens.
4. **Brute Force Defense**:
   - Failed login attempts are tracked per identifier and client IP in the `login_attempts` collection.
   - Accounts encountering 5 failed attempts within 15 minutes are temporarily locked out (HTTP `429 Too Many Requests`), backed by a 900-second TTL index.

---

## 3. Injection Defenses & Upload Hardening

1. **NoSQL Injection Defense**:
   - PyMongo queries use structured dictionary parameters with explicit type casting and Pydantic v2 schema validation. Raw unvalidated JSON dictionaries are never passed directly to database operators.
2. **CSV Formula Injection Sanitization**:
   - All exported CSV files inspect cell values and prefix any formula trigger characters (`=`, `+`, `-`, `@`, `\t`, `\r`) with a single apostrophe (`'`), preventing malicious code execution in Microsoft Excel.
3. **Upload Memory Protection**:
   - Import endpoints enforce `MAX_UPLOAD_SIZE_BYTES` (default: 15MB), reading up to `max_size + 1` bytes to detect overflow without buffering arbitrary-sized payloads into memory. Oversized payloads return HTTP `413 Request Entity Too Large`.

---

## 4. Role-Based Access Control (RBAC) Enforcement

Endpoints define explicit permission dependencies using normalized lowercase permission keys:
```python
@router.post("/orders", dependencies=[Depends(require_permission("create_order"))])
async def create_order(...):
    ...
```

Store-assigned employees inherit `store_id` constraints, restricting their operational view exclusively to their branch while company administrators access consolidated multi-store data.
