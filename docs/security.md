# Security Architecture & Tenant Isolation Guidelines

## 1. Multi-Tenant Isolation Strategy

The system is designed with defense-in-depth principles to prevent any possibility of cross-tenant data access, manipulation, or information leakage.

### 1.1 Never Trust Frontend Tenant Identifiers
The client application submits the active tenant via the `X-Company-ID` HTTP header. 
However:
1. **The backend NEVER treats `X-Company-ID` as proof of authorization.**
2. On every protected request, the backend dependency `get_tenant_context()`:
   - Identifies the authenticated user from the verified JWT / session token.
   - If the user is a `Platform Admin` (`IsSystemAdmin = 1`), access to the requested `CompanyID` is permitted.
   - For all other users, the system inspects `UserCompanies` to ensure that `(UserID, CompanyID)` exists, has `IsActive = 1`, and extracts the user's specific `RoleID` and `StoreID` within that tenant.
   - If the user is not an active member of that company, the request is immediately rejected with HTTP `403 Forbidden` (`ERR_TENANT_ACCESS_DENIED`).

### 1.2 Data Access Layer Scoping
Every SQL query executed across the domain repositories explicitly enforces tenant filtering:
```python
# CORRECT: Always scoped with parameterized CompanyID
cursor.execute(
    "SELECT CustomerID, CustomerName, Segment FROM Customers WHERE CompanyID = ? AND CustomerID = ?",
    (company_id, customer_id)
)

# INCORRECT / VULNERABLE: Lacks tenant scoping
# cursor.execute("SELECT * FROM Customers WHERE CustomerID = ?", (customer_id,))
```

### 1.3 Database Constraint Enforcement
To provide a safety net below the application layer, composite foreign keys are enforced in SQL Server:
- `Orders(StoreID, CompanyID)` -> `Stores(StoreID, CompanyID)`
- Even if a bug were introduced in application code attempting to assign Store B to an Order belonging to Company A, SQL Server rejects the write at the database engine level with a foreign key violation.

---

## 2. Authentication & Credential Security

1. **Password Hashing**:
   - Stored passwords utilize a cryptographically secure salt (32 hex bytes) and hashing algorithm (PBKDF2-HMAC-SHA256 with 100,000+ iterations or salted SHA-256 compatible with legacy system credentials).
   - Passwords are never stored in plaintext and never logged.
2. **Token Security**:
   - JWT tokens are signed using HMAC-SHA256 with a strong secret key (`SECRET_KEY`) loaded from environment variables.
   - Tokens contain short lifespans (default 60 minutes).
   - In production, authentication cookies should be configured with `HttpOnly`, `Secure` (HTTPS only), and `SameSite=Strict` or `Lax`.
3. **No Credential Logging**:
   - Password fields and authorization headers are scrubbed before logging.

---

## 3. SQL Injection Defense

- All SQL queries across the entire repository layer are parameterized using `pyodbc` positional placeholders (`?`).
- String concatenation or f-strings for SQL query parameter insertion are strictly forbidden.

---

## 4. Role-Based Access Control (RBAC) Enforcement

1. **Endpoint-Level Security**:
   Endpoints define explicit permission dependencies:
   ```python
   @router.post("/orders", dependencies=[Depends(require_permission("CREATE_ORDER"))])
   async def create_order(...):
       ...
   ```
2. **Store-Level Scoping**:
   If a user is assigned to a specific `StoreID` within `UserCompanies`, their queries automatically inherit `AND StoreID = ?` constraints, restricting their operational view to their branch.

---

## 5. Information Leakage Prevention

1. **Standardized Error Responses**:
   Unhandled internal server errors return generic error messages to the client:
   `{"detail": "An internal server error occurred.", "error_code": "ERR_INTERNAL"}`
   Detailed stack traces are recorded in backend server logs, never emitted in HTTP responses.
2. **Safe 404 vs 403 Semantics**:
   When a user requests a record ID that belongs to another tenant, the system returns `404 Not Found` (or `403 Forbidden` according to uniform policy) without confirming whether the foreign record exists.
