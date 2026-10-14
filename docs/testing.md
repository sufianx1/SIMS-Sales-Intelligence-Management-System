# Testing Strategy & Automated Test Specifications

## 1. Testing Philosophy

Testing is a first-class requirement. Every business rule, security boundary, and financial metric must be verifiable via automated test suites.

### Test Categories
1. **Unit Tests**: Test calculation routines (Sales, Profit, ProfitMargin, Pandas aggregations) and schema validation independently.
2. **Repository & Database Integration Tests**: Execute real parameterized SQL against test fixtures to ensure queries, joins, and transactions behave as expected.
3. **API & Workflow Tests**: Test endpoint request-response lifecycle with FastAPI `TestClient`.
4. **Tenant Isolation Negative Tests**: Deliberate adversarial tests proving that Tenant A cannot access or manipulate Tenant B's data under any condition.

---

## 2. Mandatory Tenant Isolation Test Suite

The following negative tests must be executed and passing before any release:

| Test Identifier | Test Case Description | Expected Result |
| :--- | :--- | :--- |
| `TEST-ISO-01` | User of Company 1 requests customer list with header `X-Company-ID: 2` | `403 Forbidden` (`ERR_TENANT_ACCESS_DENIED`) |
| `TEST-ISO-02` | User of Company 1 requests specific customer ID belonging to Company 2 | `404 Not Found` (Zero cross-tenant leakage) |
| `TEST-ISO-03` | User of Company 1 attempts to update a Product owned by Company 2 | `404 Not Found` or `403 Forbidden` |
| `TEST-ISO-04` | User of Company 1 attempts to view an Order owned by Company 2 | `404 Not Found` |
| `TEST-ISO-05` | User of Company 1 creates an Order referencing a Customer from Company 2 | `400 Bad Request` (Customer not found in tenant) |
| `TEST-ISO-06` | User of Company 1 creates an Order referencing a Store from Company 2 | `400 Bad Request` / Composite FK rejection |
| `TEST-ISO-07` | Non-admin user attempts to create a new Company via `POST /api/v1/companies` | `403 Forbidden` (`Permission denied`) |
| `TEST-ISO-08` | Store Manager assigned to Store 1 attempts to update Order belonging to Store 2 | `403 Forbidden` |
| `TEST-ISO-09` | Analytics query for Company 1 with filters explicitly verifying Company 2 data is excluded | Data contains only Company 1 records |

---

## 3. Financial Calculation Validation Tests

1. **`test_financial_margin_calculation`**:
   - Asserts that Profit Margin formula handles zero sales without DivisionByZero errors.
   - Asserts exact rounding matches `DECIMAL(10,2)`.
2. **`test_order_total_aggregation`**:
   - Verifies that joining `Orders` with `Customers` and multiple `OrderDetails` lines does not double-count order totals.

---

## 4. Test Execution Instructions

### Running Backend Tests
```bash
# Navigate to backend directory
cd backend

# Execute complete test suite with coverage
pytest tests -v --tb=short

# Run only tenant isolation tests
pytest tests/test_tenant_isolation.py -v
```

### Running Frontend Tests
```bash
# Navigate to frontend directory
cd frontend

# Run test suite
npm test
```
