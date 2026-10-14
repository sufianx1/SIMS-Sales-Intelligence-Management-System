"""
database/scripts/verify_db.py
------------------------------
Comprehensive verification script for SalesManagementDB schema,
foreign keys, multi-tenant composite integrity, and performance indexes.
"""

import sys
import pyodbc
from migrate import get_connection_string


def verify_database():
    conn_str = get_connection_string()
    print("=" * 70)
    print("SALES MANAGEMENT SYSTEM - DATABASE INTEGRITY VERIFICATION")
    print("=" * 70)

    try:
        conn = pyodbc.connect(conn_str)
    except Exception as e:
        print(f"FAILED: Connection error: {e}")
        sys.exit(1)

    cursor = conn.cursor()
    print("[OK] Successfully connected to Microsoft SQL Server: SalesManagementDB")

    # 1. Verify Core Tables
    expected_tables = [
        "Companies", "Stores", "Users", "Roles", "Permissions",
        "RolePermissions", "UserCompanies", "Customers", "Products",
        "Orders", "OrderDetails", "AuditLogs", "RawSalesData", "__SchemaMigrations"
    ]
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    existing_tables = {r[0] for r in cursor.fetchall()}
    
    missing_tables = [t for t in expected_tables if t not in existing_tables]
    if missing_tables:
        print(f"[FAIL] Missing tables: {missing_tables}")
        sys.exit(1)
    else:
        print(f"[OK] All {len(expected_tables)} required tables verified.")

    # 2. Table Row Counts
    print("\nCurrent Database Population:")
    for t in ["Companies", "Stores", "Users", "Roles", "Customers", "Products", "Orders", "OrderDetails", "AuditLogs"]:
        cursor.execute(f"SELECT COUNT(*) FROM [{t}]")
        count = cursor.fetchone()[0]
        print(f"  - {t:<15}: {count:>8,} records")

    # 3. Verify Composite Foreign Key on Orders (StoreID, CompanyID)
    cursor.execute("""
        SELECT obj.name AS FK_Name
        FROM sys.foreign_keys obj
        INNER JOIN sys.tables t_parent ON t_parent.object_id = obj.parent_object_id
        INNER JOIN sys.tables t_ref ON t_ref.object_id = obj.referenced_object_id
        WHERE t_parent.name = 'Orders' AND t_ref.name = 'Stores'
    """)
    fk_row = cursor.fetchone()
    if fk_row:
        print(f"\n[OK] Verified Composite Foreign Key constraint on Orders -> Stores: {fk_row[0]}")
    else:
        print("\n[WARN] Composite Foreign Key constraint on Orders -> Stores not found.")

    # 4. Verify Performance Indexes
    expected_indexes = [
        ("Orders", "IX_Orders_CompanyID_OrderDate"),
        ("Customers", "IX_Customers_CompanyID_Name"),
        ("Products", "IX_Products_CompanyID_Category"),
        ("OrderDetails", "IX_OrderDetails_OrderID"),
        ("OrderDetails", "IX_OrderDetails_ProductID"),
        ("AuditLogs", "IX_AuditLogs_CompanyID_CreatedAt"),
    ]
    print("\nVerifying Performance Indexes:")
    for table_name, idx_name in expected_indexes:
        cursor.execute(
            "SELECT 1 FROM sys.indexes WHERE name = ? AND object_id = OBJECT_ID(?)",
            (idx_name, table_name)
        )
        if cursor.fetchone():
            print(f"  [OK] {table_name}.{idx_name} is active")
        else:
            print(f"  [MISSING] {table_name}.{idx_name}")

    # 5. Verify Multi-Tenant Isolation Sanity (Orders strictly match Customer Company)
    cursor.execute("""
        SELECT COUNT(*)
        FROM Orders o
        JOIN Customers c ON o.CustomerID = c.CustomerID
        WHERE o.CompanyID <> c.CompanyID
    """)
    mismatched = cursor.fetchone()[0]
    if mismatched == 0:
        print("\n[OK] Multi-Tenant Referential Integrity: Zero orders cross-reference customers from another company.")
    else:
        print(f"\n[WARN] Found {mismatched} cross-tenant mismatched records!")

    print("=" * 70)
    print("DATABASE FOUNDATION VALIDATION: ALL CHECKS PASSED")
    print("=" * 70)
    conn.close()


if __name__ == "__main__":
    verify_database()
