"""
database/seeds/seed_dev_data.py
--------------------------------
Ensures standard development/testing seed accounts and company memberships
exist in SalesManagementDB with PBKDF2-HMAC-SHA256 password hashing.
Never destroys or overwrites existing production/customer data.
"""

import os
import sys
import secrets
import hashlib
from pathlib import Path
import pyodbc

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def hash_password(password: str, salt_hex: str = None) -> str:
    """Generates standard {salt}${hash} PBKDF2-HMAC-SHA256 string."""
    if not salt_hex:
        salt_bytes = secrets.token_bytes(16)
        salt_hex = salt_bytes.hex()
    else:
        salt_bytes = bytes.fromhex(salt_hex)
        
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 100000).hex()
    return f"{salt_hex}${pwd_hash}"


def get_connection():
    server = os.getenv("DB_SERVER", "localhost")
    database = os.getenv("DB_NAME", "SalesManagementDB")
    driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    trusted = os.getenv("DB_TRUSTED_CONNECTION", "true").lower() in ("true", "1", "yes")
    user = os.getenv("DB_USER", "")
    password = os.getenv("DB_PASSWORD", "")

    if trusted or not user:
        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
    else:
        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={user};PWD={password};"
        
    return pyodbc.connect(conn_str)


def seed_data():
    conn = get_connection()
    cursor = conn.cursor()
    print("Verifying and seeding core development credentials...")

    # 1. Platform Administrator
    admin_email = "shehzad@sms.example"
    cursor.execute("SELECT UserID FROM Users WHERE Email = ?", (admin_email,))
    row = cursor.fetchone()
    if not row:
        pwd_hash = hash_password("123456")
        cursor.execute(
            "INSERT INTO Users (Name, Email, PasswordHash, IsActive, IsSystemAdmin) VALUES (?, ?, ?, 1, 1)",
            ("Shehzad", admin_email, pwd_hash)
        )
        print(f"Created Platform Administrator: {admin_email}")
    else:
        print(f"Platform Administrator already exists: {admin_email} (UserID: {row[0]})")

    # 2. Verify Companies
    demo_companies = ["Superstore", "Nike", "Puma"]
    company_ids = {}
    for comp_name in demo_companies:
        cursor.execute("SELECT CompanyID FROM Companies WHERE CompanyName = ?", (comp_name,))
        comp_row = cursor.fetchone()
        if not comp_row:
            cursor.execute("INSERT INTO Companies (CompanyName, IsActive) VALUES (?, 1)", (comp_name,))
            cursor.execute("SELECT SCOPE_IDENTITY()")
            company_ids[comp_name] = int(cursor.fetchone()[0])
            print(f"Created Company: {comp_name}")
        else:
            company_ids[comp_name] = comp_row[0]

    # 3. Verify Stores
    for comp_name, comp_id in company_ids.items():
        for i in range(1, 4):
            store_name = f"{comp_name} Store {i}"
            cursor.execute("SELECT StoreID FROM Stores WHERE CompanyID = ? AND StoreName = ?", (comp_id, store_name))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO Stores (CompanyID, StoreName, Location, IsActive) VALUES (?, ?, ?, 1)",
                    (comp_id, store_name, f"{comp_name} HQ Retail {i}")
                )
                print(f"Created Store: {store_name} for {comp_name}")

    # 4. Verify Roles
    cursor.execute("SELECT RoleName, RoleID FROM Roles")
    roles_map = {r[0]: r[1] for r in cursor.fetchall()}

    # 5. Verify Demo Tenant Users
    tenant_users = [
        ("Superstore Admin", "admin@superstore.sims.local", "Superstore", "Company Admin", None),
        ("Superstore Employee", "employee@superstore.sims.local", "Superstore", "Employee", None),
        ("Nike Admin", "admin@nike.sims.local", "Nike", "Company Admin", None),
        ("Nike Employee", "employee@nike.sims.local", "Nike", "Employee", None),
        ("Puma Admin", "admin@puma.sims.local", "Puma", "Company Admin", None),
        ("Puma Employee", "employee@puma.sims.local", "Puma", "Employee", None),
    ]

    for name, email, comp_name, role_name, store_name in tenant_users:
        cursor.execute("SELECT UserID FROM Users WHERE Email = ?", (email,))
        user_row = cursor.fetchone()
        if not user_row:
            pwd_hash = hash_password("123456")
            cursor.execute(
                "INSERT INTO Users (Name, Email, PasswordHash, IsActive, IsSystemAdmin) VALUES (?, ?, ?, 1, 0)",
                (name, email, pwd_hash)
            )
            cursor.execute("SELECT SCOPE_IDENTITY()")
            user_id = int(cursor.fetchone()[0])
            print(f"Created User: {email}")
        else:
            user_id = user_row[0]

        comp_id = company_ids[comp_name]
        role_id = roles_map[role_name]
        
        cursor.execute(
            "SELECT UserCompanyID FROM UserCompanies WHERE UserID = ? AND CompanyID = ?",
            (user_id, comp_id)
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO UserCompanies (UserID, CompanyID, RoleID, IsActive) VALUES (?, ?, ?, 1)",
                (user_id, comp_id, role_id)
            )
            print(f"Assigned {email} to {comp_name} as {role_name}")

    conn.commit()
    conn.close()
    print("\nDevelopment seed accounts verified successfully.")


if __name__ == "__main__":
    seed_data()
