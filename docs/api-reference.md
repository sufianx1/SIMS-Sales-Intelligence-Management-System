# API Reference: RESTful API v1

## 1. Global Conventions & Standards

- **Base URL**: `/api/v1`
- **Format**: JSON (`Content-Type: application/json`)
- **Authentication**: Bearer Token (`Authorization: Bearer <JWT>`) or HttpOnly Cookie
- **Tenant Context Header**: `X-Company-ID: <int>` (required on all tenant-scoped endpoints)
- **Standard Success Response**: Direct entity/list payload or wrapped response
- **Standard Error Format**:
  ```json
  {
    "detail": "Descriptive error message",
    "error_code": "ERR_TENANT_ACCESS_DENIED",
    "timestamp": "2026-10-10T16:00:00Z"
  }
  ```

---

## 2. Authentication & Profile Endpoints (`/api/v1/auth`)

### `POST /api/v1/auth/login`
Authenticates user and returns JWT token plus list of permitted companies and stores.
- **Request**:
  ```json
  {
    "email": "admin@superstore.sims.local",
    "password": "Demo12345!"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "user_id": 2,
      "name": "Superstore Admin",
      "email": "admin@superstore.sims.local",
      "is_system_admin": false,
      "companies": [
        {
          "company_id": 1,
          "company_name": "Superstore",
          "role_id": 2,
          "role_name": "Company Admin",
          "store_id": null,
          "permissions": ["view_dashboard", "manage_orders", "view_orders", "manage_inventory"]
        }
      ]
    }
  }
  ```

### `GET /api/v1/auth/me`
Fetches current authenticated profile and active tenant memberships.

### `POST /api/v1/auth/logout`
Revokes active session / invalidates token.

---

## 3. Tenant Administration Endpoints

### Companies (`/api/v1/companies`)
- `GET /api/v1/companies`: List accessible companies (Platform Admin sees all; ordinary users see only member companies).
- `POST /api/v1/companies`: Provision new tenant (Platform Admin only).
- `GET /api/v1/companies/{company_id}`: Get company profile and metadata.
- `PUT /api/v1/companies/{company_id}`: Update company settings (Company Admin or Platform Admin).

### Stores (`/api/v1/stores`)
*Requires `X-Company-ID` header.*
- `GET /api/v1/stores`: List stores belonging to the active company.
- `POST /api/v1/stores`: Create store under active company (`MANAGE_STORES` permission required).
- `GET /api/v1/stores/{store_id}`: Get store detail.
- `PUT /api/v1/stores/{store_id}`: Update store details or status.

### Users & Memberships (`/api/v1/users`)
*Requires `X-Company-ID` header.*
- `GET /api/v1/users`: List users in the active company.
- `POST /api/v1/users`: Invite or assign user to company with specific Role and optional Store.
- `PUT /api/v1/users/{user_id}/status`: Activate or deactivate user company membership.
- `PUT /api/v1/users/{user_id}/role`: Reassign tenant role.

---

## 4. Operational Business Endpoints

### Customers (`/api/v1/customers`)
*Requires `X-Company-ID` header.*
- `GET /api/v1/customers?search=&segment=&page=1&limit=50`: Paginated customer directory with lifetime sales metrics.
- `GET /api/v1/customers/{customer_id}`: Single customer detail + summary statistics.
- `GET /api/v1/customers/{customer_id}/orders`: Customer purchase and order history.
- `POST /api/v1/customers`: Create customer record (`CREATE_CUSTOMER` required).
- `PUT /api/v1/customers/{customer_id}`: Update customer record.

### Products (`/api/v1/products`)
*Requires `X-Company-ID` header.*
- `GET /api/v1/products?category=&search=&page=1&limit=50`: Filterable product catalog.
- `GET /api/v1/products/{product_id}`: Product detail with lifetime units sold and revenue.
- `GET /api/v1/products/{product_id}/orders`: Order lines containing product.
- `POST /api/v1/products`: Create catalog product (`CREATE_PRODUCT` required).
- `PUT /api/v1/products/{product_id}`: Update catalog product.

### Orders (`/api/v1/orders`)
*Requires `X-Company-ID` header.*
- `GET /api/v1/orders?region=&ship_mode=&customer_id=&store_id=&start_date=&end_date=&page=1&limit=50`: Filterable orders list with aggregated line sums.
- `GET /api/v1/orders/{order_id}`: Complete order header + line items (`OrderDetails`) array.
- `POST /api/v1/orders`: Create order with line items in single database transaction.
  ```json
  {
    "order_id": "CA-2026-99001",
    "order_date": "2026-10-10",
    "ship_date": "2026-10-14",
    "ship_mode": "Standard Class",
    "customer_id": "CG-12520",
    "store_id": 2,
    "region": "West",
    "city": "Seattle",
    "state": "Washington",
    "postal_code": "98101",
    "lines": [
      {
        "product_id": "FUR-BO-10001798",
        "quantity": 2,
        "sales": 523.90,
        "discount": 0.10,
        "profit": 45.20
      }
    ]
  }
  ```
- `PUT /api/v1/orders/{order_id}`: Update order header info.
- `DELETE /api/v1/orders/{order_id}`: Cancel/delete order (`DELETE_ORDER` required).

---

## 5. Analytics & Dashboard Endpoints

### Dashboard (`/api/v1/dashboard`)
*Requires `X-Company-ID` header.*
- `GET /api/v1/dashboard/metrics`: High-level KPI cards:
  - `total_sales`: Sum of line items
  - `total_profit`: Sum of profit
  - `total_orders`: Count of distinct orders
  - `total_customers`: Count of distinct customers
  - `total_products`: Count of catalog products
- `GET /api/v1/dashboard/charts`: Category performance, regional sales, top 10 products, top 10 customers.

### Analytics (`/api/v1/analytics`)
*Requires `X-Company-ID` header.*
- `GET /api/v1/analytics/trends?interval=monthly&start_date=&end_date=`: Temporal revenue and profit timeline.
- `GET /api/v1/analytics/breakdown?group_by=category|region|segment`: Multi-dimensional aggregate breakdown.
- `GET /api/v1/analytics/matrix?category=&region=&segment=&start_date=&end_date=`: Filtered tabular dataset for dynamic Pandas slicing.

---

## 6. CSV ETL & Data Ingestion (`/api/v1/imports`)

*Requires `X-Company-ID` header and `MANAGE_COMPANIES` or `Company Admin` role.*
- `POST /api/v1/imports/validate`: Dry-run validation of uploaded CSV file. Reports schema compliance, row counts, detected issues, and unmapped fields.
- `POST /api/v1/imports/execute`: Ingests validated CSV into staging table `RawSalesData` and executes transactional normalization into the active `CompanyID`.
- `GET /api/v1/imports/history`: View past import batches, row counts, and status.
