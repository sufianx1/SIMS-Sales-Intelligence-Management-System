"""
app/db/seed.py
--------------
Deterministic demo seed script for SIMS.
Seeds exactly the 3 required companies (Superstore, Nike, Puma),
the 6 required company demo accounts (one Admin, one Employee each),
and the separate Platform Super Administrator.

Populates multi-store hierarchies, products, store-level inventory,
traceable inventory movements, customers, orders, and integration connectors.
"""

from datetime import datetime, timedelta, timezone
from pymongo.database import Database
from app.core.config import settings
from app.core.security import get_password_hash
from app.core.logging import logger
from app.db.mongo import get_db, ensure_indexes


def seed_database(db: Database, force: bool = False):
    """
    Populates MongoDB with required SIMS demo companies, users, products,
    inventory, orders, customers, and integrations.
    """
    ensure_indexes(db)

    # Check if already seeded
    if not force and db.companies.count_documents({}) >= 3:
        logger.info("Database already contains seed companies. Skipping seed.")
        return

    logger.info("Starting SIMS multi-tenant seed initialization...")

    # Drop existing collections if force=True
    if force:
        for coll in [
            "companies", "stores", "users", "memberships", "products",
            "inventory", "inventory_movements", "customers", "orders",
            "raw_imports", "structured_imports", "integrations", "sync_logs", "audit_events"
        ]:
            db[coll].delete_many({})

    demo_password_hash = get_password_hash(settings.DEMO_PASSWORD)
    now = datetime.now(timezone.utc)

    # -------------------------------------------------------------
    # 1. Companies & Stores
    # -------------------------------------------------------------
    companies_data = [
        {
            "company_id": 1,
            "company_name": "Superstore",
            "code": "SUP",
            "is_active": True,
            "created_at": now.isoformat(),
            "settings": {"currency": "USD", "timezone": "America/New_York"}
        },
        {
            "company_id": 2,
            "company_name": "Nike",
            "code": "NKE",
            "is_active": True,
            "created_at": now.isoformat(),
            "settings": {"currency": "USD", "timezone": "America/New_York"}
        },
        {
            "company_id": 3,
            "company_name": "Puma",
            "code": "PMA",
            "is_active": True,
            "created_at": now.isoformat(),
            "settings": {"currency": "USD", "timezone": "America/Los_Angeles"}
        }
    ]
    for c in companies_data:
        db.companies.update_one({"company_id": c["company_id"]}, {"$set": c}, upsert=True)

    stores_data = [
        # Superstore (3 stores)
        {
            "company_id": 1, "store_id": 1, "store_name": "Superstore Manhattan Flagship",
            "code": "SUP-NY01", "location": "500 5th Ave", "city": "New York", "state": "NY",
            "is_active": True, "created_at": now.isoformat()
        },
        {
            "company_id": 1, "store_id": 2, "store_name": "Superstore Chicago Loop",
            "code": "SUP-IL01", "location": "100 N State St", "city": "Chicago", "state": "IL",
            "is_active": True, "created_at": now.isoformat()
        },
        {
            "company_id": 1, "store_id": 3, "store_name": "Superstore LA Downtown",
            "code": "SUP-CA01", "location": "700 S Flower St", "city": "Los Angeles", "state": "CA",
            "is_active": True, "created_at": now.isoformat()
        },
        # Nike (2 stores)
        {
            "company_id": 2, "store_id": 4, "store_name": "Nike SoHo NYC",
            "code": "NKE-NY01", "location": "529 Broadway", "city": "New York", "state": "NY",
            "is_active": True, "created_at": now.isoformat()
        },
        {
            "company_id": 2, "store_id": 5, "store_name": "Nike Michigan Ave Chicago",
            "code": "NKE-IL01", "location": "669 N Michigan Ave", "city": "Chicago", "state": "IL",
            "is_active": True, "created_at": now.isoformat()
        },
        # Puma (2 stores)
        {
            "company_id": 3, "store_id": 6, "store_name": "Puma Fifth Ave NYC",
            "code": "PMA-NY01", "location": "609 5th Ave", "city": "New York", "state": "NY",
            "is_active": True, "created_at": now.isoformat()
        },
        {
            "company_id": 3, "store_id": 7, "store_name": "Puma Santana Row San Jose",
            "code": "PMA-CA01", "location": "3055 Olin Ave", "city": "San Jose", "state": "CA",
            "is_active": True, "created_at": now.isoformat()
        }
    ]
    for s in stores_data:
        db.stores.update_one(
            {"company_id": s["company_id"], "store_id": s["store_id"]},
            {"$set": s},
            upsert=True
        )

    # -------------------------------------------------------------
    # 2. Permissions Sets
    # -------------------------------------------------------------
    admin_perms = [
        "view_dashboard", "manage_orders", "view_orders", "manage_customers", "view_customers",
        "manage_products", "view_products", "manage_inventory", "view_inventory",
        "inventory_transfer", "inventory_adjust", "manage_stores", "view_stores",
        "view_analytics", "import_data", "manage_integrations", "manage_users"
    ]
    employee_perms = [
        "view_dashboard", "view_orders", "create_order", "view_customers", "create_customer",
        "view_products", "view_inventory", "inventory_adjust"
    ]

    # -------------------------------------------------------------
    # 3. Users & Tenant Memberships (Section 18 Specification)
    # -------------------------------------------------------------
    # Super Administrator (Platform Admin)
    superadmin_user = {
        "user_id": 1,
        "username": "superadmin",
        "email": "admin@platform.sims",
        "name": "Platform Super Administrator",
        "password_hash": demo_password_hash,
        "is_active": True,
        "is_system_admin": True,
        "created_at": now.isoformat()
    }
    db.users.update_one({"user_id": 1}, {"$set": superadmin_user}, upsert=True)

    demo_users = [
        # Superstore
        {
            "user_id": 2, "username": "superstore.admin", "email": "admin@superstore.sims.local",
            "name": "Superstore Admin", "company_id": 1, "company_name": "Superstore",
            "role_id": 2, "role_name": "Company Admin", "store_id": None, "store_name": None,
            "permissions": admin_perms
        },
        {
            "user_id": 3, "username": "superstore.employee", "email": "employee@superstore.sims.local",
            "name": "Superstore Employee", "company_id": 1, "company_name": "Superstore",
            "role_id": 3, "role_name": "Employee", "store_id": 1, "store_name": "Superstore Manhattan Flagship",
            "permissions": employee_perms
        },
        # Nike
        {
            "user_id": 4, "username": "nike.admin", "email": "admin@nike.sims.local",
            "name": "Nike Admin", "company_id": 2, "company_name": "Nike",
            "role_id": 2, "role_name": "Company Admin", "store_id": None, "store_name": None,
            "permissions": admin_perms
        },
        {
            "user_id": 5, "username": "nike.employee", "email": "employee@nike.sims.local",
            "name": "Nike Employee", "company_id": 2, "company_name": "Nike",
            "role_id": 3, "role_name": "Employee", "store_id": 4, "store_name": "Nike SoHo NYC",
            "permissions": employee_perms
        },
        # Puma
        {
            "user_id": 6, "username": "puma.admin", "email": "admin@puma.sims.local",
            "name": "Puma Admin", "company_id": 3, "company_name": "Puma",
            "role_id": 2, "role_name": "Company Admin", "store_id": None, "store_name": None,
            "permissions": admin_perms
        },
        {
            "user_id": 7, "username": "puma.employee", "email": "employee@puma.sims.local",
            "name": "Puma Employee", "company_id": 3, "company_name": "Puma",
            "role_id": 3, "role_name": "Employee", "store_id": 6, "store_name": "Puma Fifth Ave NYC",
            "permissions": employee_perms
        }
    ]

    for u in demo_users:
        user_doc = {
            "user_id": u["user_id"],
            "username": u["username"],
            "email": u["email"],
            "name": u["name"],
            "password_hash": demo_password_hash,
            "is_active": True,
            "is_system_admin": False,
            "created_at": now.isoformat()
        }
        db.users.update_one({"user_id": u["user_id"]}, {"$set": user_doc}, upsert=True)

        membership_doc = {
            "membership_id": u["user_id"],
            "user_id": u["user_id"],
            "company_id": u["company_id"],
            "company_name": u["company_name"],
            "role_id": u["role_id"],
            "role_name": u["role_name"],
            "store_id": u["store_id"],
            "store_name": u["store_name"],
            "permissions": u["permissions"],
            "is_active": True,
            "created_at": now.isoformat()
        }
        db.memberships.update_one(
            {"user_id": u["user_id"], "company_id": u["company_id"]},
            {"$set": membership_doc},
            upsert=True
        )

    # -------------------------------------------------------------
    # 4. Products Catalog (Company-isolated with cost basis)
    # -------------------------------------------------------------
    products_seed = {
        1: [  # Superstore
            {"product_id": "SUP-TEC-001", "product_name": "Canon ImageCLASS Advanced Copier", "category": "Technology", "sub_category": "Copiers", "sku": "SUP-TEC-001", "unit_cost": 850.00, "unit_price": 1299.99},
            {"product_id": "SUP-TEC-002", "product_name": "Logitech Wireless Ergonomic Keyboard", "category": "Technology", "sub_category": "Accessories", "sku": "SUP-TEC-002", "unit_cost": 45.00, "unit_price": 89.99},
            {"product_id": "SUP-FUR-001", "product_name": "Executive High-Back Mesh Chair", "category": "Furniture", "sub_category": "Chairs", "sku": "SUP-FUR-001", "unit_cost": 160.00, "unit_price": 289.00},
            {"product_id": "SUP-FUR-002", "product_name": "Adjustable Standing Desk 60x30", "category": "Furniture", "sub_category": "Tables", "sku": "SUP-FUR-002", "unit_cost": 290.00, "unit_price": 499.50},
            {"product_id": "SUP-OFF-001", "product_name": "Heavy Duty Steel Filing Cabinet", "category": "Office Supplies", "sub_category": "Storage", "sku": "SUP-OFF-001", "unit_cost": 80.00, "unit_price": 149.00},
            {"product_id": "SUP-OFF-002", "product_name": "Premium Multi-Purpose Paper (10 Reams)", "category": "Office Supplies", "sub_category": "Paper", "sku": "SUP-OFF-002", "unit_cost": 25.00, "unit_price": 44.99},
        ],
        2: [  # Nike
            {"product_id": "NKE-SH-001", "product_name": "Nike Air Zoom Pegasus 40", "category": "Footwear", "sub_category": "Running", "sku": "NKE-SH-001", "unit_cost": 65.00, "unit_price": 139.99},
            {"product_id": "NKE-SH-002", "product_name": "Air Jordan 1 Retro High OG", "category": "Footwear", "sub_category": "Basketball", "sku": "NKE-SH-002", "unit_cost": 90.00, "unit_price": 180.00},
            {"product_id": "NKE-APP-001", "product_name": "Nike Dri-FIT Legend T-Shirt", "category": "Apparel", "sub_category": "Tops", "sku": "NKE-APP-001", "unit_cost": 12.00, "unit_price": 35.00},
            {"product_id": "NKE-APP-002", "product_name": "Nike Sportswear Club Fleece Hoodie", "category": "Apparel", "sub_category": "Sweatshirts", "sku": "NKE-APP-002", "unit_cost": 28.00, "unit_price": 65.00},
            {"product_id": "NKE-ACC-001", "product_name": "Nike Brasilia Training Duffel Bag", "category": "Accessories", "sub_category": "Bags", "sku": "NKE-ACC-001", "unit_cost": 18.00, "unit_price": 42.00},
        ],
        3: [  # Puma
            {"product_id": "PMA-SH-001", "product_name": "Puma Velocity NITRO 3 Running Shoes", "category": "Footwear", "sub_category": "Running", "sku": "PMA-SH-001", "unit_cost": 60.00, "unit_price": 135.00},
            {"product_id": "PMA-SH-002", "product_name": "Puma Suede Classic XXI Sneakers", "category": "Footwear", "sub_category": "Classics", "sku": "PMA-SH-002", "unit_cost": 35.00, "unit_price": 75.00},
            {"product_id": "PMA-APP-001", "product_name": "Puma ESS Logo Heather Tee", "category": "Apparel", "sub_category": "Tops", "sku": "PMA-APP-001", "unit_cost": 10.00, "unit_price": 28.00},
            {"product_id": "PMA-APP-002", "product_name": "Puma T7 Track Jacket", "category": "Apparel", "sub_category": "Jackets", "sku": "PMA-APP-002", "unit_cost": 32.00, "unit_price": 75.00},
        ]
    }

    for comp_id, prods in products_seed.items():
        for p in prods:
            doc = {**p, "company_id": comp_id, "is_active": True, "created_at": now.isoformat()}
            db.products.update_one(
                {"company_id": comp_id, "product_id": p["product_id"]},
                {"$set": doc},
                upsert=True
            )

    # -------------------------------------------------------------
    # 5. Multi-Store Inventory on Hand & Movements
    # -------------------------------------------------------------
    # Quantities per store (with intentionally varying levels: normal, low-stock, and out-of-stock)
    inventory_levels = [
        # Superstore Store 1
        {"company_id": 1, "store_id": 1, "product_id": "SUP-TEC-001", "qty": 18, "min": 5, "max": 50},
        {"company_id": 1, "store_id": 1, "product_id": "SUP-TEC-002", "qty": 4, "min": 10, "max": 100},  # LOW STOCK
        {"company_id": 1, "store_id": 1, "product_id": "SUP-FUR-001", "qty": 12, "min": 5, "max": 40},
        {"company_id": 1, "store_id": 1, "product_id": "SUP-FUR-002", "qty": 0, "min": 3, "max": 20},   # OUT OF STOCK
        {"company_id": 1, "store_id": 1, "product_id": "SUP-OFF-001", "qty": 15, "min": 5, "max": 30},
        {"company_id": 1, "store_id": 1, "product_id": "SUP-OFF-002", "qty": 85, "min": 20, "max": 200},
        # Superstore Store 2
        {"company_id": 1, "store_id": 2, "product_id": "SUP-TEC-001", "qty": 8, "min": 5, "max": 30},
        {"company_id": 1, "store_id": 2, "product_id": "SUP-TEC-002", "qty": 35, "min": 10, "max": 80},
        {"company_id": 1, "store_id": 2, "product_id": "SUP-FUR-001", "qty": 2, "min": 5, "max": 30},   # LOW STOCK
        {"company_id": 1, "store_id": 2, "product_id": "SUP-FUR-002", "qty": 7, "min": 3, "max": 15},
        {"company_id": 1, "store_id": 2, "product_id": "SUP-OFF-001", "qty": 11, "min": 5, "max": 25},
        {"company_id": 1, "store_id": 2, "product_id": "SUP-OFF-002", "qty": 40, "min": 20, "max": 150},
        # Superstore Store 3
        {"company_id": 1, "store_id": 3, "product_id": "SUP-TEC-001", "qty": 14, "min": 5, "max": 30},
        {"company_id": 1, "store_id": 3, "product_id": "SUP-TEC-002", "qty": 20, "min": 10, "max": 60},
        {"company_id": 1, "store_id": 3, "product_id": "SUP-FUR-001", "qty": 9, "min": 5, "max": 25},
        {"company_id": 1, "store_id": 3, "product_id": "SUP-FUR-002", "qty": 5, "min": 3, "max": 15},
        {"company_id": 1, "store_id": 3, "product_id": "SUP-OFF-001", "qty": 8, "min": 5, "max": 20},
        {"company_id": 1, "store_id": 3, "product_id": "SUP-OFF-002", "qty": 60, "min": 20, "max": 150},

        # Nike Store 4
        {"company_id": 2, "store_id": 4, "product_id": "NKE-SH-001", "qty": 45, "min": 10, "max": 100},
        {"company_id": 2, "store_id": 4, "product_id": "NKE-SH-002", "qty": 3, "min": 8, "max": 50},   # LOW STOCK
        {"company_id": 2, "store_id": 4, "product_id": "NKE-APP-001", "qty": 80, "min": 20, "max": 150},
        {"company_id": 2, "store_id": 4, "product_id": "NKE-APP-002", "qty": 30, "min": 10, "max": 60},
        {"company_id": 2, "store_id": 4, "product_id": "NKE-ACC-001", "qty": 25, "min": 5, "max": 50},
        # Nike Store 5
        {"company_id": 2, "store_id": 5, "product_id": "NKE-SH-001", "qty": 28, "min": 10, "max": 80},
        {"company_id": 2, "store_id": 5, "product_id": "NKE-SH-002", "qty": 15, "min": 8, "max": 40},
        {"company_id": 2, "store_id": 5, "product_id": "NKE-APP-001", "qty": 50, "min": 20, "max": 120},
        {"company_id": 2, "store_id": 5, "product_id": "NKE-APP-002", "qty": 0, "min": 10, "max": 50},   # OUT OF STOCK
        {"company_id": 2, "store_id": 5, "product_id": "NKE-ACC-001", "qty": 18, "min": 5, "max": 40},

        # Puma Store 6
        {"company_id": 3, "store_id": 6, "product_id": "PMA-SH-001", "qty": 35, "min": 10, "max": 80},
        {"company_id": 3, "store_id": 6, "product_id": "PMA-SH-002", "qty": 24, "min": 8, "max": 60},
        {"company_id": 3, "store_id": 6, "product_id": "PMA-APP-001", "qty": 5, "min": 15, "max": 100}, # LOW STOCK
        {"company_id": 3, "store_id": 6, "product_id": "PMA-APP-002", "qty": 16, "min": 5, "max": 40},
        # Puma Store 7
        {"company_id": 3, "store_id": 7, "product_id": "PMA-SH-001", "qty": 19, "min": 10, "max": 60},
        {"company_id": 3, "store_id": 7, "product_id": "PMA-SH-002", "qty": 12, "min": 8, "max": 50},
        {"company_id": 3, "store_id": 7, "product_id": "PMA-APP-001", "qty": 40, "min": 15, "max": 80},
        {"company_id": 3, "store_id": 7, "product_id": "PMA-APP-002", "qty": 9, "min": 5, "max": 30},
    ]

    for inv in inventory_levels:
        inv_id = f"{inv['company_id']}-{inv['store_id']}-{inv['product_id']}"
        doc = {
            "inventory_id": inv_id,
            "company_id": inv["company_id"],
            "store_id": inv["store_id"],
            "product_id": inv["product_id"],
            "quantity_on_hand": inv["qty"],
            "min_threshold": inv["min"],
            "max_threshold": inv["max"],
            "last_updated": now.isoformat()
        }
        db.inventory.update_one(
            {"company_id": inv["company_id"], "store_id": inv["store_id"], "product_id": inv["product_id"]},
            {"$set": doc},
            upsert=True
        )

    # Initial Traceable Movements
    sample_movements = [
        # Initial receipts
        {
            "movement_id": "MOV-001", "company_id": 1, "from_store_id": None, "to_store_id": 1,
            "product_id": "SUP-TEC-001", "quantity": 25, "movement_type": "RECEIPT",
            "reason": "Initial Purchase Order Supplier Receipt", "performed_by": 2,
            "timestamp": (now - timedelta(days=20)).isoformat()
        },
        # Store transfer from Store 1 to Store 2
        {
            "movement_id": "MOV-002", "company_id": 1, "from_store_id": 1, "to_store_id": 2,
            "product_id": "SUP-TEC-001", "quantity": 7, "movement_type": "TRANSFER",
            "reason": "Inter-Store Inventory Rebalance to Chicago Loop", "performed_by": 2,
            "timestamp": (now - timedelta(days=5)).isoformat()
        },
        # Stock adjustment for broken/damaged item
        {
            "movement_id": "MOV-003", "company_id": 1, "from_store_id": 1, "to_store_id": None,
            "product_id": "SUP-TEC-002", "quantity": -1, "movement_type": "ADJUSTMENT",
            "reason": "Floor Display Damage Write-Off", "performed_by": 3,
            "timestamp": (now - timedelta(days=2)).isoformat()
        },
        # Nike receipt
        {
            "movement_id": "MOV-004", "company_id": 2, "from_store_id": None, "to_store_id": 4,
            "product_id": "NKE-SH-001", "quantity": 50, "movement_type": "RECEIPT",
            "reason": "Autumn Season Production Intake", "performed_by": 4,
            "timestamp": (now - timedelta(days=15)).isoformat()
        },
        # Puma inter-store transfer
        {
            "movement_id": "MOV-005", "company_id": 3, "from_store_id": 6, "to_store_id": 7,
            "product_id": "PMA-SH-001", "quantity": 10, "movement_type": "TRANSFER",
            "reason": "Santana Row Stock Replenishment", "performed_by": 6,
            "timestamp": (now - timedelta(days=4)).isoformat()
        }
    ]
    for m in sample_movements:
        db.inventory_movements.update_one({"movement_id": m["movement_id"]}, {"$set": m}, upsert=True)

    # -------------------------------------------------------------
    # 6. Customers
    # -------------------------------------------------------------
    customers_seed = {
        1: [
            {"customer_id": "SUP-CUST-001", "customer_name": "Claire Gute", "segment": "Consumer", "city": "Philadelphia", "state": "PA", "country": "United States"},
            {"customer_id": "SUP-CUST-002", "customer_name": "Brosina Hoffman", "segment": "Consumer", "city": "Los Angeles", "state": "CA", "country": "United States"},
            {"customer_id": "SUP-CUST-003", "customer_name": "Darrin Martin", "segment": "Corporate", "city": "Chicago", "state": "IL", "country": "United States"},
            {"customer_id": "SUP-CUST-004", "customer_name": "Sean O'Donnell", "segment": "Home Office", "city": "Fort Lauderdale", "state": "FL", "country": "United States"},
        ],
        2: [
            {"customer_id": "NKE-CUST-001", "customer_name": "Marcus Vance", "segment": "Athlete", "city": "New York", "state": "NY", "country": "United States"},
            {"customer_id": "NKE-CUST-002", "customer_name": "Elena Rostova", "segment": "Consumer", "city": "Chicago", "state": "IL", "country": "United States"},
            {"customer_id": "NKE-CUST-003", "customer_name": "Apex Fitness Club", "segment": "Corporate", "city": "Boston", "state": "MA", "country": "United States"},
        ],
        3: [
            {"customer_id": "PMA-CUST-001", "customer_name": "David Thorne", "segment": "Consumer", "city": "San Jose", "state": "CA", "country": "United States"},
            {"customer_id": "PMA-CUST-002", "customer_name": "Sarah Jenkins", "segment": "Consumer", "city": "New York", "state": "NY", "country": "United States"},
        ]
    }
    for comp_id, custs in customers_seed.items():
        for c in custs:
            doc = {**c, "company_id": comp_id, "is_active": True, "created_at": now.isoformat()}
            db.customers.update_one(
                {"company_id": comp_id, "customer_id": c["customer_id"]},
                {"$set": doc},
                upsert=True
            )

    # -------------------------------------------------------------
    # 7. Realistic Orders and Order Items
    # -------------------------------------------------------------
    orders_seed = [
        # Superstore Orders
        {
            "order_id": "SUP-ORD-2026-001", "company_id": 1, "store_id": 1, "customer_id": "SUP-CUST-001",
            "order_date": (now - timedelta(days=2)).strftime("%Y-%m-%d"),
            "ship_date": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
            "ship_mode": "Standard Class",
            "lines": [
                {
                    "line_id": 1, "product_id": "SUP-TEC-001", "product_name": "Canon ImageCLASS Advanced Copier",
                    "category": "Technology", "quantity": 1, "unit_price": 1299.99, "unit_cost": 850.00,
                    "sales": 1299.99, "discount": 0.0, "profit": 449.99
                },
                {
                    "line_id": 2, "product_id": "SUP-OFF-002", "product_name": "Premium Multi-Purpose Paper (10 Reams)",
                    "category": "Office Supplies", "quantity": 2, "unit_price": 44.99, "unit_cost": 25.00,
                    "sales": 89.98, "discount": 0.0, "profit": 39.98
                }
            ],
            "total_sales": 1389.97, "total_cost": 900.00, "total_profit": 489.97, "total_quantity": 3
        },
        {
            "order_id": "SUP-ORD-2026-002", "company_id": 1, "store_id": 2, "customer_id": "SUP-CUST-003",
            "order_date": (now - timedelta(days=4)).strftime("%Y-%m-%d"),
            "ship_date": (now - timedelta(days=3)).strftime("%Y-%m-%d"),
            "ship_mode": "Second Class",
            "lines": [
                {
                    "line_id": 1, "product_id": "SUP-FUR-001", "product_name": "Executive High-Back Mesh Chair",
                    "category": "Furniture", "quantity": 2, "unit_price": 289.00, "unit_cost": 160.00,
                    "sales": 578.00, "discount": 0.05, "profit": 229.10
                }
            ],
            "total_sales": 549.10, "total_cost": 320.00, "total_profit": 229.10, "total_quantity": 2
        },
        {
            "order_id": "SUP-ORD-2026-003", "company_id": 1, "store_id": 3, "customer_id": "SUP-CUST-002",
            "order_date": (now - timedelta(days=7)).strftime("%Y-%m-%d"),
            "ship_date": (now - timedelta(days=5)).strftime("%Y-%m-%d"),
            "ship_mode": "First Class",
            "lines": [
                {
                    "line_id": 1, "product_id": "SUP-FUR-002", "product_name": "Adjustable Standing Desk 60x30",
                    "category": "Furniture", "quantity": 1, "unit_price": 499.50, "unit_cost": 290.00,
                    "sales": 499.50, "discount": 0.0, "profit": 209.50
                },
                {
                    "line_id": 2, "product_id": "SUP-TEC-002", "product_name": "Logitech Wireless Ergonomic Keyboard",
                    "category": "Technology", "quantity": 1, "unit_price": 89.99, "unit_cost": 45.00,
                    "sales": 89.99, "discount": 0.0, "profit": 44.99
                }
            ],
            "total_sales": 589.49, "total_cost": 335.00, "total_profit": 254.49, "total_quantity": 2
        },

        # Nike Orders
        {
            "order_id": "NKE-ORD-2026-001", "company_id": 2, "store_id": 4, "customer_id": "NKE-CUST-001",
            "order_date": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
            "ship_date": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
            "ship_mode": "Same Day",
            "lines": [
                {
                    "line_id": 1, "product_id": "NKE-SH-002", "product_name": "Air Jordan 1 Retro High OG",
                    "category": "Footwear", "quantity": 1, "unit_price": 180.00, "unit_cost": 90.00,
                    "sales": 180.00, "discount": 0.0, "profit": 90.00
                },
                {
                    "line_id": 2, "product_id": "NKE-APP-002", "product_name": "Nike Sportswear Club Fleece Hoodie",
                    "category": "Apparel", "quantity": 1, "unit_price": 65.00, "unit_cost": 28.00,
                    "sales": 65.00, "discount": 0.0, "profit": 37.00
                }
            ],
            "total_sales": 245.00, "total_cost": 118.00, "total_profit": 127.00, "total_quantity": 2
        },
        {
            "order_id": "NKE-ORD-2026-002", "company_id": 2, "store_id": 5, "customer_id": "NKE-CUST-003",
            "order_date": (now - timedelta(days=6)).strftime("%Y-%m-%d"),
            "ship_date": (now - timedelta(days=4)).strftime("%Y-%m-%d"),
            "ship_mode": "Standard Class",
            "lines": [
                {
                    "line_id": 1, "product_id": "NKE-SH-001", "product_name": "Nike Air Zoom Pegasus 40",
                    "category": "Footwear", "quantity": 5, "unit_price": 139.99, "unit_cost": 65.00,
                    "sales": 699.95, "discount": 0.10, "profit": 304.95
                }
            ],
            "total_sales": 629.95, "total_cost": 325.00, "total_profit": 304.95, "total_quantity": 5
        },

        # Puma Orders
        {
            "order_id": "PMA-ORD-2026-001", "company_id": 3, "store_id": 6, "customer_id": "PMA-CUST-002",
            "order_date": (now - timedelta(days=3)).strftime("%Y-%m-%d"),
            "ship_date": (now - timedelta(days=2)).strftime("%Y-%m-%d"),
            "ship_mode": "Standard Class",
            "lines": [
                {
                    "line_id": 1, "product_id": "PMA-SH-001", "product_name": "Puma Velocity NITRO 3 Running Shoes",
                    "category": "Footwear", "quantity": 1, "unit_price": 135.00, "unit_cost": 60.00,
                    "sales": 135.00, "discount": 0.0, "profit": 75.00
                },
                {
                    "line_id": 2, "product_id": "PMA-APP-002", "product_name": "Puma T7 Track Jacket",
                    "category": "Apparel", "quantity": 1, "unit_price": 75.00, "unit_cost": 32.00,
                    "sales": 75.00, "discount": 0.0, "profit": 43.00
                }
            ],
            "total_sales": 210.00, "total_cost": 92.00, "total_profit": 118.00, "total_quantity": 2
        }
    ]

    for ord_doc in orders_seed:
        db.orders.update_one(
            {"company_id": ord_doc["company_id"], "order_id": ord_doc["order_id"]},
            {"$set": ord_doc},
            upsert=True
        )

    # -------------------------------------------------------------
    # 8. Integrations & Reference Connectors (Section 12 Specification)
    # -------------------------------------------------------------
    integrations_seed = [
        {
            "integration_id": "INT-SUP-POS01",
            "company_id": 1,
            "store_id": 1,
            "name": "Superstore POS Cloud Sync (Store 1)",
            "connector_type": "POS_REST_API",
            "is_active": True,
            "config": {
                "endpoint_url": "https://api.pos-terminal.internal/v2",
                "sync_interval_minutes": 30,
                "read_only": True,
                "idempotent_key_prefix": "POS-NY01"
            },
            "last_sync_at": (now - timedelta(minutes=15)).isoformat(),
            "sync_status": "SUCCESS",
            "created_at": (now - timedelta(days=30)).isoformat()
        },
        {
            "integration_id": "INT-NKE-ECOM",
            "company_id": 2,
            "store_id": None,
            "name": "Nike E-Commerce Webhook Connector",
            "connector_type": "ECOMMERCE_WEBHOOK",
            "is_active": True,
            "config": {
                "webhook_path": "/webhooks/nike/orders",
                "secret_key_ref": "ENV:NKE_WEBHOOK_SECRET",
                "auto_capture_inventory": True
            },
            "last_sync_at": (now - timedelta(hours=2)).isoformat(),
            "sync_status": "SUCCESS",
            "created_at": (now - timedelta(days=20)).isoformat()
        },
        {
            "integration_id": "INT-PMA-MOCK",
            "company_id": 3,
            "store_id": 6,
            "name": "Retail Pro Connector (Reference Mock)",
            "connector_type": "MOCK_STORE_CONNECTOR",
            "is_active": False,
            "config": {
                "notes": "Configured for local validation and staging tests"
            },
            "last_sync_at": None,
            "sync_status": "PENDING",
            "created_at": (now - timedelta(days=10)).isoformat()
        }
    ]

    for ig in integrations_seed:
        db.integrations.update_one(
            {"integration_id": ig["integration_id"]},
            {"$set": ig},
            upsert=True
        )

    # Seed sync logs for reference POS connector
    sample_sync_log = {
        "log_id": "SYNC-LOG-001",
        "integration_id": "INT-SUP-POS01",
        "company_id": 1,
        "sync_type": "INCREMENTAL",
        "records_processed": 14,
        "errors": [],
        "status": "SUCCESS",
        "started_at": (now - timedelta(minutes=16)).isoformat(),
        "completed_at": (now - timedelta(minutes=15)).isoformat(),
        "cursor_checkpoint": "2026-10-14T07:15:00Z"
    }
    db.sync_logs.update_one({"log_id": sample_sync_log["log_id"]}, {"$set": sample_sync_log}, upsert=True)

    logger.info("SIMS database successfully seeded with Superstore, Nike, Puma demo environments.")


if __name__ == "__main__":
    db = get_db()
    seed_database(db, force=True)
    print("Seeding completed successfully.")
